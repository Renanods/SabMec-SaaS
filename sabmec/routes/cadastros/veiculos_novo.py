from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.cadastros.veiculos import veiculos_bp
from sabmec.forms.veiculos_forms import FormVeiculo
from sabmec.models.veiculos import Veiculo
from sabmec.models.pessoas import Pessoa


def texto_upper(valor):
    if not valor:
        return None

    valor = valor.strip()
    return valor.upper() if valor else None


def inteiro_ou_none(valor):
    if not valor:
        return None

    try:
        return int(valor)
    except ValueError:
        return None


def carregar_choices_pessoas(form):
    form.pessoa_id.choices = [(0, "Selecione...")] + [
        (pessoa.id, pessoa.nome)
        for pessoa in Pessoa.query
            .filter(Pessoa.ativo.is_(True), Pessoa.eh_cliente.is_(True))
            .order_by(Pessoa.nome)
            .all()
    ]


def renderizar_veiculos_novo(form):
    return render_template(
        "cadastros/veiculos_novo.html",
        form=form,
    )


@veiculos_bp.route("/veiculos/novo", methods=["GET", "POST"])
@login_required
def veiculos_novo():
    form = FormVeiculo()
    carregar_choices_pessoas(form)

    if request.method == "POST":
        try:
            pessoa_id = request.form.get("pessoa_id", type=int)
            placa = texto_upper(request.form.get("placa"))
            marca = texto_upper(request.form.get("marca"))
            modelo = texto_upper(request.form.get("modelo"))

            if not pessoa_id or pessoa_id == 0:
                flash("Selecione o proprietário.", "warning")
                return renderizar_veiculos_novo(form)

            if not placa:
                flash("Informe a placa.", "warning")
                return renderizar_veiculos_novo(form)

            if not marca:
                flash("Informe a marca.", "warning")
                return renderizar_veiculos_novo(form)

            if not modelo:
                flash("Informe o modelo.", "warning")
                return renderizar_veiculos_novo(form)

            placa_existente = Veiculo.query.filter_by(placa=placa).first()

            if placa_existente:
                flash("Já existe um veículo cadastrado com esta placa.", "warning")
                return renderizar_veiculos_novo(form)

            veiculo = Veiculo(
                pessoa_id=pessoa_id,
                placa=placa,
                marca=marca,
                modelo=modelo,
                ano_fabricacao=inteiro_ou_none(request.form.get("ano_fabricacao")),
                ano_modelo=inteiro_ou_none(request.form.get("ano_modelo")),
                cor=texto_upper(request.form.get("cor")),
                chassi=texto_upper(request.form.get("chassi")),
                renavam=texto_upper(request.form.get("renavam")),
                observacao=texto_upper(request.form.get("observacao")),
                ativo=True if request.form.get("ativo") else False,
            )

            db.session.add(veiculo)
            db.session.commit()

            flash("Veículo cadastrado com sucesso.", "success")
            return redirect(url_for("veiculos.veiculos"))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao cadastrar veículo: {erro}", "danger")

    return renderizar_veiculos_novo(form)
