from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from sabmec import db
from sabmec.models.compra import (
    Compra,
    STATUS_COMPRA_CANCELADA,
    STATUS_COMPRA_CONFIRMADA,
)
from sabmec.routes.comercial.compras.compras import compras_bp
from sabmec.routes.comercial.compras.compras_utils import (
    aplicar_estoque_item,
    criar_produto_compra,
    dados_conferencia,
    garantir_schema_compras,
    gerar_contas_pagar,
    parse_xml_nfe,
)


@compras_bp.route("/compras/<int:id>/conferir", methods=["GET"])
@login_required
def compras_conferir_nota(id):
    garantir_schema_compras()

    compra = Compra.query.get_or_404(id)

    if compra.status == STATUS_COMPRA_CANCELADA:
        flash("Esta nota esta cancelada e nao pode ser conferida.", "warning")
        return redirect(url_for("compras.compras", pesquisar=1))

    dados, itens = dados_conferencia(compra)

    return render_template(
        "comercial/compras/compras_conferir.html",
        compra=compra,
        dados=dados,
        fornecedor_status="Existente",
        itens=itens,
    )


@compras_bp.route("/compras/<int:id>/confirmar", methods=["POST"])
@login_required
def compras_confirmar(id):
    garantir_schema_compras()

    compra = Compra.query.get_or_404(id)

    if compra.status == STATUS_COMPRA_CONFIRMADA:
        flash("Esta nota ja foi confirmada.", "warning")
        return redirect(url_for("compras.compras", pesquisar=1))

    if compra.status == STATUS_COMPRA_CANCELADA:
        flash("Esta nota esta cancelada.", "warning")
        return redirect(url_for("compras.compras", pesquisar=1))

    try:
        dados = parse_xml_nfe(compra.xml_original)

        if len(compra.itens) != len(dados["itens"]):
            raise ValueError("A quantidade de itens da nota nao confere com o XML importado.")

        for index, item_xml in enumerate(dados["itens"]):
            compra_item = compra.itens[index]
            acao = request.form.get(f"acao_item_{index}")

            if acao == "vincular":
                item_id = int(request.form.get(f"vinculo_item_id_{index}", 0))
                if not item_id:
                    raise ValueError(f"Selecione um produto para vincular o item {index + 1}.")

                aplicar_estoque_item(compra_item, item_xml, item_id)
                continue

            novo_produto = criar_produto_compra(item_xml)
            compra_item.item_id = novo_produto.id

        gerar_contas_pagar(compra, dados)

        compra.status = STATUS_COMPRA_CONFIRMADA
        db.session.commit()

        flash(f"Entrada da NF {compra.numero_nota} confirmada. Estoque e contas a pagar atualizados.", "success")
        return redirect(url_for("compras.compras", pesquisar=1, tipo_busca="nota", busca=compra.numero_nota))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao confirmar entrada: {erro}", "danger")
        return redirect(url_for("compras.compras_conferir_nota", id=compra.id))
