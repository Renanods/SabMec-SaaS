from sqlalchemy import select, func
from flask import redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.cadastros.condicao_pagamento import condicao_pgto_bp
from sabmec.models.cond_forma_pgto import CondicaoPagamento, CondicaoPagamentoParcela


TABELAS_INTERNAS_CONDICAO = {
    "condicoes_pagamento_parcela",
}


def buscar_vinculos_bloqueantes_condicao(condicao_id):
    vinculos = []

    for tabela in db.metadata.tables.values():
        if tabela.name == "condicoes_pagamento" or tabela.name in TABELAS_INTERNAS_CONDICAO:
            continue

        for fk in tabela.foreign_keys:
            if fk.column.table.name == "condicoes_pagamento":
                total = db.session.execute(
                    select(func.count())
                    .select_from(tabela)
                    .where(fk.parent == condicao_id)
                ).scalar()

                if total:
                    vinculos.append(f"{tabela.name} ({total})")

    return vinculos


def excluir_dados_internos_condicao(condicao_id):
    CondicaoPagamentoParcela.query.filter_by(condicao_id=condicao_id).delete()


@condicao_pgto_bp.route("/condicao/<int:id>/excluir", methods=["POST"])
@login_required
def condicao_pgto_excluir(id):
    condicao = CondicaoPagamento.query.get_or_404(id)

    try:
        vinculos = buscar_vinculos_bloqueantes_condicao(condicao.id)

        if vinculos:
            condicao.ativo = False
            db.session.commit()

            flash(
                "Esta condição possui vínculos no sistema e não pode ser excluída. "
                "Ela foi inativada para preservar o histórico.",
                "warning",
            )
            return redirect(url_for("condicao.condicao_pgto"))

        excluir_dados_internos_condicao(condicao.id)
        db.session.delete(condicao)
        db.session.commit()

        return redirect(url_for("condicao.condicao_pgto"))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao excluir condição de pagamento: {erro}", "danger")
        return redirect(url_for("condicao.condicao_pgto"))
