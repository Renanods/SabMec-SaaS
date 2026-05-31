from flask import render_template, redirect, url_for, flash
from flask_login import login_required

from sabmec.routes.comercial.os.os import os_bp
from sabmec.models.ordem_servico import OrdemServico
from sabmec.models.contas_receber import ContaReceber


def situacao_os(ordem):
    if not ordem.status:
        return ""

    return (ordem.status.situacao or "").strip().lower()


@os_bp.route("/os/<int:id>/detalhar")
@login_required
def os_detalhar(id):
    ordem = OrdemServico.query.get_or_404(id)

    contas_receber = ContaReceber.query.filter_by(
        origem="OS",
        referencia_id=ordem.id,
    ).order_by(
        ContaReceber.vencimento.asc(),
        ContaReceber.id.asc(),
    ).all()

    situacao = situacao_os(ordem)
    os_cancelada = situacao in ["cancelado", "cancelada"]

    if not contas_receber and not os_cancelada:
        flash("Essa OS ainda não foi faturada. O detalhamento financeiro só fica disponível após o faturamento ou cancelamento.", "warning")
        return redirect(url_for("os.os"))

    total_receber = sum((conta.valor or 0) for conta in contas_receber)
    total_pago = sum((conta.valor_pago or 0) for conta in contas_receber)
    total_restante = total_receber - total_pago

    return render_template(
        "comercial/os_detalhar.html",
        ordem=ordem,
        contas_receber=contas_receber,
        total_receber=total_receber,
        total_pago=total_pago,
        total_restante=total_restante,
    )
