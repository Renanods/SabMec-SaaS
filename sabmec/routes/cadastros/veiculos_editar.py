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


def carregar_choices_pessoas(form, pessoa_atual_id=None):
    pessoas = Pessoa.query.filter(Pessoa.ativo.is_(True), Pessoa.eh_cliente.is_(True)).order_by(Pessoa.nome).all()

    if pessoa_atual_id:
        pessoa_atual = Pessoa.query.get(pessoa_atual_id)
        if pessoa_atual and pessoa_atual not in pessoas:
            pessoas.append(pessoa_atual)

    form.pessoa_id.choices = [(0, "Selecione...")] + [
        (pessoa.id, pessoa.nome)
        for pessoa in pessoas
    ]


def renderizar_veiculos_editar(veiculo, form):
    return render_template(
        "cadastros/veiculos_editar.html",
        veiculo=veiculo,
        form=form,
    )


@veiculos_bp.route("/veiculos/<int:id>/editar", methods=["GET", "POST"])
@login_required
def veiculos_editar(id):
    veiculo = Veiculo.query.get_or_404(id)

    form = FormVeiculo()
    carregar_choices_pessoas(form, veiculo.pessoa_id)

    if request.method == "GET":
        form.pessoa_id.data = veiculo.pessoa_id
        form.placa.data = veiculo.placa
        form.marca.data = veiculo.marca
        form.modelo.data = veiculo.modelo
        form.ano_fabricacao.data = veiculo.ano_fabricacao
        form.ano_modelo.data = veiculo.ano_modelo
        form.cor.data = veiculo.cor
        form.chassi.data = veiculo.chassi
        form.renavam.data = veiculo.renavam
        form.observacao.data = veiculo.observacao
        form.ativo.data = veiculo.ativo

    if request.method == "POST":
        try:
            pessoa_id = request.form.get("pessoa_id", type=int)
            placa = texto_upper(request.form.get("placa"))
            marca = texto_upper(request.form.get("marca"))
            modelo = texto_upper(request.form.get("modelo"))

            if not pessoa_id or pessoa_id == 0:
                flash("Selecione o proprietário.", "warning")
                return renderizar_veiculos_editar(veiculo, form)

            if not placa:
                flash("Informe a placa.", "warning")
                return renderizar_veiculos_editar(veiculo, form)

            if not marca:
                flash("Informe a marca.", "warning")
                return renderizar_veiculos_editar(veiculo, form)

            if not modelo:
                flash("Informe o modelo.", "warning")
                return renderizar_veiculos_editar(veiculo, form)

            placa_existente = Veiculo.query.filter(
                Veiculo.placa == placa,
                Veiculo.id != veiculo.id,
            ).first()

            if placa_existente:
                flash("Já existe outro veículo cadastrado com esta placa.", "warning")
                return renderizar_veiculos_editar(veiculo, form)

            veiculo.pessoa_id = pessoa_id
            veiculo.placa = placa
            veiculo.marca = marca
            veiculo.modelo = modelo
            veiculo.ano_fabricacao = inteiro_ou_none(request.form.get("ano_fabricacao"))
            veiculo.ano_modelo = inteiro_ou_none(request.form.get("ano_modelo"))
            veiculo.cor = texto_upper(request.form.get("cor"))
            veiculo.chassi = texto_upper(request.form.get("chassi"))
            veiculo.renavam = texto_upper(request.form.get("renavam"))
            veiculo.observacao = texto_upper(request.form.get("observacao"))
            veiculo.ativo = True if request.form.get("ativo") else False

            db.session.commit()

            flash("Veículo atualizado com sucesso.", "success")
            return redirect(url_for("veiculos.veiculos_editar", id=veiculo.id))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao atualizar veículo: {erro}", "danger")

    return renderizar_veiculos_editar(veiculo, form)