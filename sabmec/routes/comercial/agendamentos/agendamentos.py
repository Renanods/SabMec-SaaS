from flask import Blueprint, render_template, request
from flask_login import login_required

from sabmec.models.agendamento import Agendamento
from sabmec.models.pessoas import Pessoa
from sabmec.models.veiculos import Veiculo
from sabmec.models.tipos import Status


agendamentos_bp = Blueprint("agendamentos", __name__)


@agendamentos_bp.route("/agendamentos")
@login_required
def agendamentos():
    pesquisar = request.args.get("pesquisar")
    busca = request.args.get("busca", "").strip()
    status_filtro = request.args.get("status", "")  # valor = ID do status como string
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")

    # Carrega todos os status de agendamento para o filtro do template
    todos_status = Status.query.order_by(Status.id).all()

    if not pesquisar:
        return render_template(
            "comercial/agendamentos/agendamentos.html",
            agendamentos=[],
            busca=busca,
            status=status_filtro,
            data_inicio=data_inicio,
            data_fim=data_fim,
            todos_status=todos_status,
        )

    query = Agendamento.query.join(Pessoa).join(Veiculo)

    if busca:
        busca_upper = busca.upper()
        query = query.filter(Pessoa.nome.ilike(f"%{busca_upper}%"))

    if status_filtro:
        try:
            status_id_filtro = int(status_filtro)
            query = query.filter(Agendamento.status_id == status_id_filtro)
        except ValueError:
            pass

    if data_inicio:
        query = query.filter(Agendamento.data >= data_inicio)

    if data_fim:
        query = query.filter(Agendamento.data <= data_fim)

    lista_agendamentos = query.order_by(Agendamento.data.desc(), Agendamento.hora.desc()).all()

    return render_template(
        "comercial/agendamentos/agendamentos.html",
        agendamentos=lista_agendamentos,
        busca=busca,
        status=status_filtro,
        data_inicio=data_inicio,
        data_fim=data_fim,
        todos_status=todos_status,
    )




from sabmec.routes.comercial.agendamentos import agendamentos_api, agendamentos_cancelar, agendamentos_concluir, agendamentos_converter_os, agendamentos_editar, agendamentos_novo