from decimal import Decimal

from flask import redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.comercial.os.os import os_bp
from sabmec.models.tipos import Status
from sabmec.models.ordem_servico import OrdemServico
from sabmec.models.contas_receber import ContaReceber


def buscar_status(nome):
    return Status.query.filter(Status.situacao.ilike(nome)).first()


def situacao(objeto_com_status):
    if not objeto_com_status or not objeto_com_status.status:
        return ""

    return (objeto_com_status.status.situacao or "").strip().lower()


def devolver_estoque(ordem):
    for ordem_item in ordem.itens:
        if ordem_item.tipo != "Produto":
            continue

        if not ordem_item.item or not ordem_item.item.mercadoria:
            continue

        estoque_atual = float(ordem_item.item.mercadoria.estoque or 0)
        quantidade = float(ordem_item.quantidade or 0)
    
        ordem_item.item.mercadoria.estoque = estoque_atual + quantidade


@os_bp.route("/os/<int:id>/cancelar", methods=["POST"])
@login_required
def os_cancelar(id):
    ordem = OrdemServico.query.get_or_404(id)

    status_cancelado = buscar_status("CANCELADO")

    if not status_cancelado:
        flash("Cadastre o status CANCELADO antes de cancelar uma OS.", "danger")
        return redirect(url_for("os.os"))

    situacao_os = situacao(ordem)

    if situacao_os == "cancelado" or situacao_os == "cancelada":
        flash("Essa OS já está cancelada.", "warning")
        return redirect(url_for("os.os"))

    contas = ContaReceber.query.filter_by(
        origem="OS",
        referencia_id=ordem.id,
    ).all()

    try:
        if situacao_os == "pendente":
            ordem.status_id = status_cancelado.id

            for conta in contas:
                if situacao(conta) in ["pendente", "cancelado", "cancelada"]:
                    conta.status_id = status_cancelado.id

            db.session.commit()
            flash("OS cancelada com sucesso.", "success")
            return redirect(url_for("os.os"))

        if situacao_os == "atendido" or situacao_os == "atendida":
            tem_conta_baixada = any(
                situacao(conta) in ["atendido", "atendida", "pago", "paga"]
                for conta in contas
            )

            if tem_conta_baixada:
                flash(
                    "Não é possível cancelar esta OS porque existe conta a receber já atendida/paga. Faça o estorno do contas a receber antes de cancelar.",
                    "warning",
                )
                return redirect(url_for("os.os"))

            devolver_estoque(ordem)

            ordem.status_id = status_cancelado.id

            for conta in contas:
                conta.status_id = status_cancelado.id

            db.session.commit()

            return redirect(url_for("os.os"))

        flash("Essa OS não pode ser cancelada nessa situação.", "warning")
        return redirect(url_for("os.os"))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao cancelar OS: {erro}", "danger")
        return redirect(url_for("os.os"))
