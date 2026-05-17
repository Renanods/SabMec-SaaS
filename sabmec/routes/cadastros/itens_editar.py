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
        return Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def inteiro_ou_zero(valor):
    if not valor:
        return 0

    try:
        return int(valor)
    except ValueError:
        return 0


def renderizar_itens_editar(item, form_item, form_produto, form_servico):
    return render_template(
        "cadastros/itens_editar.html",
        item=item,
        form_item=form_item,
        form_produto=form_produto,
        form_servico=form_servico,
    )


@itens_bp.route("/itens/<int:id>/editar", methods=["GET", "POST"])
@login_required
def itens_editar(id):
    item = Item.query.get_or_404(id)

    form_item = FormItem()
    form_produto = FormItemProduto()
    form_servico = FormItemServico()

    if request.method == "GET":
        form_item.nome.data = item.nome
        form_item.preco.data = item.preco
        form_item.tipo.data = item.tipo
        form_item.ativo.data = item.ativo

        if item.mercadoria:
            form_produto.custo.data = item.mercadoria.custo
            form_produto.estoque.data = item.mercadoria.estoque

    if request.method == "POST":
        try:
            nome = texto_upper(request.form.get("nome"))
            preco = decimal_ou_none(request.form.get("preco"))
            tipo = request.form.get("tipo")
            ativo = True if request.form.get("ativo") else False

            if not nome:
                flash("Informe o nome do item.", "warning")
                return renderizar_itens_editar(item, form_item, form_produto, form_servico)

            if preco is None:
                flash("Informe o preço de venda.", "warning")
                return renderizar_itens_editar(item, form_item, form_produto, form_servico)

            if tipo not in ["Produto", "Servico"]:
                flash("Selecione o tipo do item.", "warning")
                return renderizar_itens_editar(item, form_item, form_produto, form_servico)

            item.nome = nome
            item.preco = preco
            item.tipo = tipo
            item.ativo = ativo

            if tipo == "Produto":
                custo = decimal_ou_none(request.form.get("custo"))
                estoque = inteiro_ou_zero(request.form.get("estoque"))

                if custo is None:
                    flash("Informe o custo do produto.", "warning")
                    return renderizar_itens_editar(item, form_item, form_produto, form_servico)

                if item.servico:
                    db.session.delete(item.servico)

                if not item.mercadoria:
                    item.mercadoria = ItemMercadoria(item_id=item.id)

                item.mercadoria.custo = custo
                item.mercadoria.estoque = estoque

            if tipo == "Servico":
                if item.mercadoria:
                    db.session.delete(item.mercadoria)

                if not item.servico:
                    item.servico = ItemServico(item_id=item.id)

            db.session.commit()

            flash("Item atualizado com sucesso.", "success")
            return redirect(url_for("itens.itens_editar", id=item.id))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao atualizar item: {erro}", "danger")

    return renderizar_itens_editar(item, form_item, form_produto, form_servico)
