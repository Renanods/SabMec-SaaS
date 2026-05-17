from decimal import Decimal, InvalidOperation
from flask_login import login_required
from flask import render_template, request, redirect, url_for, flash
from sabmec import db
from sabmec.routes.cadastros.itens import itens_bp
from sabmec.forms.itens_forms import FormItem, FormItemProduto, FormItemServico
from sabmec.models.item import Item, ItemMercadoria, ItemServico


def texto_upper(valor):
    if not valor:
        return None

    valor = valor.strip()
    return valor.upper() if valor else None


def decimal_ou_none(valor):
    if not valor:
        return None

    try:
        valor = str(valor).replace(",", ".")
        return Decimal(valor)
    except (InvalidOperation, ValueError):
        return None


def inteiro_ou_zero(valor):
    if not valor:
        return 0

    try:
        return int(valor)
    except ValueError:
        return 0


def renderizar_itens_novo(form_item, form_produto, form_servico):
    return render_template(
        "cadastros/itens_novo.html",
        form_item=form_item,
        form_produto=form_produto,
        form_servico=form_servico,
    )


@itens_bp.route("/itens/novo", methods=["GET", "POST"])
@login_required
def itens_novo():
    form_item = FormItem()
    form_produto = FormItemProduto()
    form_servico = FormItemServico()

    if request.method == "POST":
        try:
            nome = texto_upper(request.form.get("nome"))
            preco = decimal_ou_none(request.form.get("preco"))
            tipo = request.form.get("tipo")
            ativo = True if request.form.get("ativo") else False

            if not nome:
                flash("Informe o nome do item.", "warning")
                return renderizar_itens_novo(form_item, form_produto, form_servico)

            if preco is None:
                flash("Informe o preço de venda.", "warning")
                return renderizar_itens_novo(form_item, form_produto, form_servico)

            if tipo not in ["Produto", "Servico"]:
                flash("Selecione o tipo do item.", "warning")
                return renderizar_itens_novo(form_item, form_produto, form_servico)

            item = Item(
                nome=nome,
                preco=preco,
                tipo=tipo,
                ativo=ativo,
            )

            db.session.add(item)
            db.session.flush()

            if tipo == "Produto":
                custo = decimal_ou_none(request.form.get("custo"))
                estoque = inteiro_ou_zero(request.form.get("estoque"))

                if custo is None:
                    flash("Informe o custo do produto.", "warning")
                    db.session.rollback()
                    return renderizar_itens_novo(form_item, form_produto, form_servico)

                mercadoria = ItemMercadoria(
                    item_id=item.id,
                    estoque=estoque,
                    custo=custo,
                )

                db.session.add(mercadoria)

            if tipo == "Servico":
                servico = ItemServico(
                    item_id=item.id,
                )

                db.session.add(servico)

            db.session.commit()

            flash("Item cadastrado com sucesso.", "success")
            return redirect(url_for("itens.itens"))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao cadastrar item: {erro}", "danger")

    return renderizar_itens_novo(form_item, form_produto, form_servico)

