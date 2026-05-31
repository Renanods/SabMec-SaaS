from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime

from sabmec.forms.agendamento_forms import FormAgendamento
from sabmec.models.agendamento import Agendamento, STATUS_CONCLUIDO_ID, STATUS_CANCELADO_ID
from sabmec.routes.comercial.agendamentos.agendamentos import agendamentos_bp
from sabmec.routes.comercial.agendamentos.agendamentos_novo import nome_cliente, verificar_conflito
from sabmec.models.pessoas import Pessoa
from sabmec.models.veiculos import Veiculo

def carregar_choices(form, cliente_id=None):
    clientes = Pessoa.query.filter(
        Pessoa.ativo.is_(True),
        Pessoa.eh_cliente.is_(True),
    ).order_by(Pessoa.nome).all()
    form.cliente_id.choices = [(0, "Selecione...")] + [(c.id, c.nome) for c in clientes]

    # Veículos
    if cliente_id and cliente_id > 0:
        veiculos = Veiculo.query.filter_by(pessoa_id=cliente_id, ativo=True).order_by(Veiculo.placa).all()
        form.veiculo_id.choices = [(0, "Selecione...")] + [(v.id, f"{v.placa} - {v.modelo}") for v in veiculos]
    else:
        form.veiculo_id.choices = [(0, "Selecione um cliente primeiro")]




@agendamentos_bp.route("/agendamentos/<int:id>/editar", methods=["GET", "POST"])
@login_required
def agendamento_editar(id):
    from sabmec import db
    agendamento = Agendamento.query.get_or_404(id)
    
    if agendamento.status_id in [STATUS_CONCLUIDO_ID, STATUS_CANCELADO_ID]:
        flash("Não é possível editar um agendamento concluído ou cancelado.", "warning")
        return redirect(url_for('agendamentos.agendamento_detalhar', id=agendamento.id))
        
    form = FormAgendamento(obj=agendamento)
    
    cliente_id = request.form.get("cliente_id", type=int) if request.method == "POST" else agendamento.cliente_id
    carregar_choices(form, cliente_id)
    cliente_nome_val = nome_cliente(cliente_id)
    
    if request.method == "POST":
        if form.cliente_id.data == 0:
            flash("Selecione um cliente.", "warning")
            return render_template("comercial/agendamentos/agendamento_editar.html", form=form, agendamento=agendamento, cliente_nome=cliente_nome_val)
            
        if form.veiculo_id.data == 0:
            flash("Selecione um veículo.", "warning")
            return render_template("comercial/agendamentos/agendamento_editar.html", form=form, agendamento=agendamento, cliente_nome=cliente_nome_val)
            
        if verificar_conflito(form.data.data, form.hora.data, agendamento.id):
            flash("Já existe um agendamento para este horário.", "danger")
            return render_template("comercial/agendamentos/agendamento_editar.html", form=form, agendamento=agendamento, cliente_nome=cliente_nome_val)
            
        agendamento.cliente_id = form.cliente_id.data
        agendamento.veiculo_id = form.veiculo_id.data
        agendamento.data = form.data.data
        agendamento.hora = form.hora.data
        agendamento.problema_relatado = form.problema_relatado.data.upper() if form.problema_relatado.data else None
        agendamento.observacoes = form.observacoes.data.upper() if form.observacoes.data else None
        
        db.session.commit()
        flash("Agendamento atualizado com sucesso!", "success")
        return redirect(url_for('agendamentos.agendamento_detalhar', id=agendamento.id))
        
    return render_template("comercial/agendamentos/agendamento_editar.html", form=form, agendamento=agendamento, cliente_nome=cliente_nome_val)

@agendamentos_bp.route("/agendamentos/<int:id>/detalhar")
@login_required
def agendamento_detalhar(id):
    agendamento = Agendamento.query.get_or_404(id)
    return render_template("comercial/agendamentos/agendamento_detalhar.html", agendamento=agendamento)
