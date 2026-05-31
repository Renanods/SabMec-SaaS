from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from sabmec.routes.comercial.agendamentos.agendamentos import agendamentos_bp

from sabmec.forms.agendamento_forms import FormAgendamento
from sabmec.models.agendamento import Agendamento, STATUS_AGENDADO_ID, STATUS_CANCELADO_ID
from sabmec.models.pessoas import Pessoa


def nome_cliente(cliente_id):
    if not cliente_id:
        return ""

    cliente = Pessoa.query.get(cliente_id)
    if not cliente:
        return ""

    cliente_nome = f"#{cliente.id} - {cliente.nome}"
    if cliente.documento_fiscal:
        cliente_nome += f" ({cliente.documento_fiscal})"

    return cliente_nome


def verificar_conflito(data, hora, agendamento_id=None):
    query = Agendamento.query.filter_by(data=data, hora=hora).filter(Agendamento.status_id != STATUS_CANCELADO_ID)
    if agendamento_id:
        query = query.filter(Agendamento.id != agendamento_id)
    return query.first()


@agendamentos_bp.route("/agendamentos/novo", methods=["GET", "POST"])
@login_required
def agendamento_novo():
    from sabmec import db
    from sabmec.routes.comercial.agendamentos.agendamentos_editar import carregar_choices

    form = FormAgendamento()
    
    cliente_id = request.form.get("cliente_id", type=int) if request.method == "POST" else None
    carregar_choices(form, cliente_id)
    cliente_nome_val = nome_cliente(cliente_id)
    
    if request.method == "POST":
        if form.cliente_id.data == 0:
            flash("Selecione um cliente.", "warning")
            return render_template("comercial/agendamentos/agendamento_novo.html", form=form, cliente_nome=cliente_nome_val)
            
        if form.veiculo_id.data == 0:
            flash("Selecione um veículo.", "warning")
            return render_template("comercial/agendamentos/agendamento_novo.html", form=form, cliente_nome=cliente_nome_val)
            
        if verificar_conflito(form.data.data, form.hora.data):
            flash("Já existe um agendamento para este horário.", "danger")
            return render_template("comercial/agendamentos/agendamento_novo.html", form=form, cliente_nome=cliente_nome_val)
            
        agendamento = Agendamento(
            cliente_id=form.cliente_id.data,
            veiculo_id=form.veiculo_id.data,
            data=form.data.data,
            hora=form.hora.data,
            problema_relatado=form.problema_relatado.data.upper() if form.problema_relatado.data else None,
            observacoes=form.observacoes.data.upper() if form.observacoes.data else None,
            status_id=STATUS_AGENDADO_ID
        )
        db.session.add(agendamento)
        db.session.commit()
        flash("Agendamento criado com sucesso!", "success")
        return redirect(url_for('agendamentos.agendamentos', pesquisar=1))
        
    return render_template("comercial/agendamentos/agendamento_novo.html", form=form, cliente_nome=cliente_nome_val)
