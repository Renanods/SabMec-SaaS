from datetime import datetime

from flask import flash, redirect, url_for
from flask_login import login_required

from sabmec import db
from sabmec.models.compra import Compra, STATUS_COMPRA_CANCELADA, STATUS_COMPRA_CONFIRMADA
from sabmec.routes.comercial.compras.compras import compras_bp
from sabmec.routes.comercial.compras.compras_utils import (
    decimal_ou_zero,
    excluir_contas_pagar_compra,
    garantir_schema_compras,
)


@compras_bp.route("/compras/<int:id>/cancelar", methods=["POST"])
@login_required
def compras_cancelar(id):
    garantir_schema_compras()

    compra = Compra.query.get_or_404(id)

    if compra.status == STATUS_COMPRA_CANCELADA:
        flash("Esta nota ja esta cancelada.", "warning")
        return redirect(url_for("compras.compras", pesquisar=1))

    try:
        if compra.status == STATUS_COMPRA_CONFIRMADA:
            for compra_item in compra.itens:
                if compra_item.item and compra_item.item.mercadoria:
                    compra_item.item.mercadoria.estoque = (
                        compra_item.item.mercadoria.estoque or 0
                    ) - int(decimal_ou_zero(compra_item.quantidade))

            excluir_contas_pagar_compra(compra)

        compra.status = STATUS_COMPRA_CANCELADA
        compra.cancelado_em = datetime.utcnow()

        db.session.commit()

        flash(f"Nota NF {compra.numero_nota} cancelada. Estoque e contas a pagar foram estornados quando aplicavel.", "success")
        return redirect(url_for("compras.compras", pesquisar=1, tipo_busca="nota", busca=compra.numero_nota))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao cancelar nota: {erro}", "danger")
        return redirect(url_for("compras.compras", pesquisar=1))
