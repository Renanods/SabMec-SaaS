from flask import redirect, url_for, flash
from flask_login import login_required

from sabmec.models.agendamento import Agendamento, STATUS_CONCLUIDO_ID, STATUS_CANCELADO_ID
from sabmec.routes.comercial.agendamentos.agendamentos import agendamentos_bp


@agendamentos_bp.route("/agendamentos/<int:id>/cancelar", methods=["POST"])
@login_required
def agendamento_cancelar(id):
    from sabmec import db

    agendamento = Agendamento.query.get_or_404(id)
    
    if agendamento.status_id in [STATUS_CONCLUIDO_ID, STATUS_CANCELADO_ID]:
        flash("Este agendamento já está concluído ou cancelado.", "warning")
        return redirect(url_for('agendamentos.agendamentos', pesquisar=1))
        
    agendamento.status_id = STATUS_CANCELADO_ID
    db.session.commit()
    flash("Agendamento cancelado.", "success")
    return redirect(url_for('agendamentos.agendamentos', pesquisar=1))