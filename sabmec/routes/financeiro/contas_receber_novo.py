from decimal import Decimal, InvalidOperation

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.financeiro.contas_receber import contas_receber_bp
from sabmec.forms.contas_receber_forms import FormContaReceber
from sabmec.models.contas_receber import ContaReceber
from sabmec.models.pessoas import Pessoa
from sabmec.models.tipos import Status


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
    form.cliente_id.choices = [(0, "Selecione...")] + [
        (pessoa.id, f"#{pessoa.id} - {pessoa.nome}")
        for pessoa in Pessoa.query
            .filter(Pessoa.ativo.is_(True), Pessoa.eh_cliente.is_(True))
            .order_by(Pessoa.nome.asc())
            .all()
    ]


@contas_receber_bp.route("/contas-receber/novo", methods=["GET", "POST"])
@login_required
def contas_receber_novo():
    form = FormContaReceber()
    carregar_choices(form)

    status_pendente = buscar_status("PENDENTE")

    if not status_pendente:
        flash("Cadastre o status PENDENTE antes de criar contas a receber.", "danger")
        return redirect(url_for("contas_receber.contas_receber"))

    cliente_nome = ""
    cliente_id = request.form.get("cliente_id", type=int) if request.method == "POST" else request.args.get("cliente_id", type=int)
    if cliente_id:
        cliente = Pessoa.query.get(cliente_id)
        if cliente:
            cliente_nome = f"#{cliente.id} - {cliente.nome}"

    if request.method == "GET":
        form.origem.data = "AVULSO"
        return render_template("financeiro/contas_receber_novo.html", form=form, cliente_nome=cliente_nome)

    try:
        descricao = texto_upper(request.form.get("descricao"))
        valor = decimal_ou_zero(request.form.get("valor"))
        vencimento = request.form.get("vencimento")

        if not cliente_id or cliente_id == 0:
            flash("Selecione o cliente.", "warning")
            return render_template("financeiro/contas_receber_novo.html", form=form, cliente_nome=cliente_nome)

        if not descricao:
            flash("Informe a descrição.", "warning")
            return render_template("financeiro/contas_receber_novo.html", form=form, cliente_nome=cliente_nome)

        if valor <= 0:
            flash("O valor deve ser maior que zero.", "warning")
            return render_template("financeiro/contas_receber_novo.html", form=form, cliente_nome=cliente_nome)

        if not vencimento:
            flash("Informe o vencimento.", "warning")
            return render_template("financeiro/contas_receber_novo.html", form=form, cliente_nome=cliente_nome)

        conta = ContaReceber(
            cliente_id=cliente_id,
            status_id=status_pendente.id,
            origem="AVULSO",
            referencia_id=None,
            descricao=descricao,
            parcela=texto_upper(request.form.get("parcela")) or "1/1",
            valor=valor,
            vencimento=form.vencimento.data,
            observacao=texto_upper(request.form.get("observacao")),
        )

        db.session.add(conta)
        db.session.commit()

        return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao cadastrar conta a receber: {erro}", "danger")

    return render_template("financeiro/contas_receber_novo.html", form=form, cliente_nome=cliente_nome)
