from decimal import Decimal, InvalidOperation

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required

from sabmec import db
from sabmec.forms.contas_pagar_forms import FormContaPagar
from sabmec.models.contas_pagar import ContaPagar
from sabmec.models.pessoas import Pessoa
from sabmec.models.tipos import Status
from sabmec.routes.financeiro.contas_pagar import contas_pagar_bp


def decimal_ou_zero(valor):
    if valor in [None, ""]:
        return Decimal("0")

    valor = str(valor).strip()

    try:
        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")

        return Decimal(valor)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def texto_upper(valor):
    if not valor:
        return None

    valor = valor.strip()
    return valor.upper() if valor else None


def buscar_status(nome):
    return Status.query.filter(Status.situacao.ilike(nome)).first()


def carregar_choices(form):
    form.fornecedor_id.choices = [(0, "Selecione...")] + [
        (pessoa.id, f"#{pessoa.id} - {pessoa.nome}")
        for pessoa in Pessoa.query
            .filter(Pessoa.ativo.is_(True), Pessoa.eh_fornecedor.is_(True))
            .order_by(Pessoa.nome.asc())
            .all()
    ]


@contas_pagar_bp.route("/contas-pagar/novo", methods=["GET", "POST"])
@login_required
def contas_pagar_novo():
    form = FormContaPagar()
    carregar_choices(form)

    status_pendente = buscar_status("PENDENTE")

    if not status_pendente:
        flash("Cadastre o status PENDENTE antes de criar contas a pagar.", "danger")
        return redirect(url_for("contas_pagar.contas_pagar"))

    fornecedor_nome = ""
    fornecedor_id = request.form.get("fornecedor_id", type=int) if request.method == "POST" else request.args.get("fornecedor_id", type=int)
    if fornecedor_id:
        fornecedor = Pessoa.query.get(fornecedor_id)
        if fornecedor:
            fornecedor_nome = f"#{fornecedor.id} - {fornecedor.nome}"

    if request.method == "GET":
        form.origem.data = "AVULSO"
        return render_template("financeiro/contas_pagar_novo.html", form=form, fornecedor_nome=fornecedor_nome)

    try:
        descricao = texto_upper(request.form.get("descricao"))
        valor = decimal_ou_zero(request.form.get("valor"))
        vencimento = request.form.get("vencimento")

        if not fornecedor_id or fornecedor_id == 0:
            flash("Selecione o fornecedor.", "warning")
            return render_template("financeiro/contas_pagar_novo.html", form=form, fornecedor_nome=fornecedor_nome)

        if not descricao:
            flash("Informe a descricao.", "warning")
            return render_template("financeiro/contas_pagar_novo.html", form=form, fornecedor_nome=fornecedor_nome)

        if valor <= 0:
            flash("O valor deve ser maior que zero.", "warning")
            return render_template("financeiro/contas_pagar_novo.html", form=form, fornecedor_nome=fornecedor_nome)

        if not vencimento:
            flash("Informe o vencimento.", "warning")
            return render_template("financeiro/contas_pagar_novo.html", form=form, fornecedor_nome=fornecedor_nome)

        conta = ContaPagar(
            fornecedor_id=fornecedor_id,
            status_id=status_pendente.id,
            origem="AVULSO",
            referencia_id=None,
            descricao=descricao,
            parcela=texto_upper(request.form.get("parcela")) or "1/1",
            documento=texto_upper(request.form.get("documento")),
            valor=valor,
            vencimento=form.vencimento.data,
            observacao=texto_upper(request.form.get("observacao")),
        )

        db.session.add(conta)
        db.session.commit()

        return redirect(url_for("contas_pagar.contas_pagar", pesquisar=1))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao cadastrar conta a pagar: {erro}", "danger")

    return render_template("financeiro/contas_pagar_novo.html", form=form, fornecedor_nome=fornecedor_nome)


@contas_pagar_bp.route("/contas-pagar/buscar-fornecedores")
@login_required
def buscar_fornecedores():
    termo = request.args.get("q", "").strip().upper()
    tipo_busca = request.args.get("tipo_busca", "nome")

    query = Pessoa.query.filter(
        Pessoa.ativo.is_(True),
        Pessoa.eh_fornecedor.is_(True),
    )

    if termo:
        if tipo_busca == "id" and termo.isdigit():
            query = query.filter(Pessoa.id == int(termo))
        elif tipo_busca == "documento":
            documento = "".join(filter(str.isdigit, termo))
            query = query.filter(Pessoa.documento_fiscal.ilike(f"%{documento}%"))
        else:
            query = query.filter(Pessoa.nome.ilike(f"%{termo}%"))

    fornecedores = query.order_by(Pessoa.id.asc()).limit(50).all()

    return jsonify({
        "fornecedores": [
            {
                "id": f.id,
                "nome": f.nome,
                "documento": f.documento_fiscal,
            }
            for f in fornecedores
        ]
    })
