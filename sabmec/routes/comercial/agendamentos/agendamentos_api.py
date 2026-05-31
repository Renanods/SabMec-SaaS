from flask import render_template, jsonify, request
from flask_login import login_required
from datetime import datetime

from sabmec.routes.comercial.agendamentos.agendamentos import agendamentos_bp
from sabmec.models.agendamento import Agendamento, STATUS_CONCLUIDO_ID, STATUS_CANCELADO_ID

@agendamentos_bp.route("/agendamentos/calendario")
@login_required
def agendamentos_calendario():
    return render_template("comercial/agendamentos/agendamentos_calendario.html")


@agendamentos_bp.route("/agendamentos/api/eventos")
@login_required
def api_eventos():
    start = request.args.get('start')
    end = request.args.get('end')
    
    query = Agendamento.query
    if start:
        query = query.filter(Agendamento.data >= start[:10])
    if end:
        query = query.filter(Agendamento.data <= end[:10])
        
    agendamentos = query.all()
    
    eventos = []
    for ag in agendamentos:
        cor = "#ffc107"  # Agendado (amarelo)
        text_cor = "#212529"
        if ag.status_id == STATUS_CONCLUIDO_ID:
            cor = '#198754'  # Concluído (verde)
            text_cor = '#ffffff'
        elif ag.status_id == STATUS_CANCELADO_ID:
            cor = '#dc3545'  # Cancelado (vermelho)
            text_cor = '#ffffff'
            
        data_hora = f"{ag.data}T{ag.hora}"
        
        eventos.append({
            'id': ag.id,
            'title': f"{ag.cliente.nome} - {ag.veiculo.modelo}",
            'start': data_hora,
            'color': cor,
            'textColor': text_cor,
            'url': f"/agendamentos/{ag.id}/detalhar"
        })
        
    return jsonify(eventos)