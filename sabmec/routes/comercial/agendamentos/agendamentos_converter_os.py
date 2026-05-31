from flask import redirect, url_for, flash
from flask_login import login_required

from sabmec.models.agendamento import Agendamento, STATUS_CONCLUIDO_ID
from sabmec.routes.comercial.agendamentos.agendamentos import agendamentos_bp
from sabmec.models.ordem_servico import OrdemServico
from sabmec.models.tipos import Status


@agendamentos_bp.route("/agendamentos/<int:id>/criar-os", methods=["POST"])
@login_required
def agendamento_criar_os(id):
    from sabmec import db

    agendamento = Agendamento.query.get_or_404(id)
    
    if agendamento.status_id != STATUS_CONCLUIDO_ID:
        flash("O agendamento precisa estar Concluído para criar uma Ordem de Serviço.", "warning")
        return redirect(url_for('agendamentos.agendamento_detalhar', id=agendamento.id))
        
    if agendamento.ordem_servico_id:
        flash("Uma Ordem de Serviço já foi criada para este agendamento.", "warning")
        return redirect(url_for('agendamentos.agendamento_detalhar', id=agendamento.id))
        
    status_os = Status.query.filter(Status.situacao.ilike("PENDENTE")).first()
    if not status_os:
        status_os = Status.query.order_by(Status.id.asc()).first()
        
    nova_os = OrdemServico(
        cliente_id=agendamento.cliente_id,
        veiculo_id=agendamento.veiculo_id,
        status_id=status_os.id,
        data_previsao=agendamento.data,
        relato_cliente=agendamento.problema_relatado,
        subtotal_produtos=0,
        subtotal_servicos=0,
        desconto=0,
        acrescimo=0,
        total=0
    )
    
    db.session.add(nova_os)
    db.session.flush() # Para obter o ID da nova OS
    
    agendamento.ordem_servico_id = nova_os.id
    
    db.session.commit()
    
    flash("Ordem de Serviço criada com sucesso! Você pode adicionar os itens e serviços agora.", "success")
    return redirect(url_for('os.os_editar', id=nova_os.id))