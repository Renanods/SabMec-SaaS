from sqlalchemy import select, func
from flask import redirect, url_for, flash
from flask_login import login_required
from sabmec import db
from sabmec.routes.cadastros.itens import itens_bp
from sabmec.models.item import Item, ItemMercadoria, ItemServico


TABELAS_INTERNAS_ITEM = {
    "itens_mercadoria",
    "itens_servico",
}


def buscar_vinculos_bloqueantes_item(item_id):
    vinculos = []

    for tabela in db.metadata.tables.values():
        if tabela.name == "itens" or tabela.name in TABELAS_INTERNAS_ITEM:
            continue

        for fk in tabela.foreign_keys:
            if fk.column.table.name == "itens":
                total = db.session.execute(
                    select(func.count())
                    .select_from(tabela)
                    .where(fk.parent == item_id)
                ).scalar()

                if total:
                    vinculos.append(f"{tabela.name} ({total})")

    return vinculos


def excluir_dados_internos_item(item_id):
    ItemMercadoria.query.filter_by(item_id=item_id).delete()
    ItemServico.query.filter_by(item_id=item_id).delete()


@itens_bp.route("/itens/<int:id>/excluir", methods=["POST"])
@login_required
def itens_excluir(id):
    item = Item.query.get_or_404(id)

    try:
        vinculos = buscar_vinculos_bloqueantes_item(item.id)

        if vinculos:
            item.ativo = False
            db.session.commit()

            flash(
                "Este item possui vínculos no sistema e não pode ser excluído. "
                "Ele foi inativado para preservar o histórico.",
                "warning",
            )
            return redirect(url_for("itens.itens"))

        excluir_dados_internos_item(item.id)
        db.session.delete(item)
        db.session.commit()

        return redirect(url_for("itens.itens"))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao excluir item: {erro}", "danger")
        return redirect(url_for("itens.itens"))
