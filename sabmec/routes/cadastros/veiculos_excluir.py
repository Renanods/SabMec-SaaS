from sqlalchemy import select, func
from flask import redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.cadastros.veiculos import veiculos_bp
from sabmec.models.veiculos import Veiculo


def buscar_vinculos_bloqueantes_veiculo(veiculo_id):
    vinculos = []

    for tabela in db.metadata.tables.values():
        if tabela.name == "veiculos":
            continue

        for fk in tabela.foreign_keys:
            if fk.column.table.name == "veiculos":
                total = db.session.execute(
                    select(func.count())
                    .select_from(tabela)
                    .where(fk.parent == veiculo_id)
                ).scalar()

                if total:
                    vinculos.append(f"{tabela.name} ({total})")

    return vinculos


@veiculos_bp.route("/veiculos/<int:id>/excluir", methods=["POST"])
@login_required
def veiculos_excluir(id):
    veiculo = Veiculo.query.get_or_404(id)

    try:
        vinculos = buscar_vinculos_bloqueantes_veiculo(veiculo.id)

        if vinculos:
            veiculo.ativo = False
            db.session.commit()

            flash(
                "Este veículo possui vínculos no sistema e não pode ser excluído. "
                "Ele foi inativado para preservar o histórico.",
                "warning",
            )
            return redirect(url_for("veiculos.veiculos"))

        db.session.delete(veiculo)
        db.session.commit()

        flash("Veículo excluído com sucesso.", "success")
        return redirect(url_for("veiculos.veiculos"))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao excluir veículo: {erro}", "danger")
        return redirect(url_for("veiculos.veiculos"))
