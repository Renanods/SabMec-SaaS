from flask import Blueprint, render_template, request
from flask_login import login_required

from sabmec.models.ordem_servico import OrdemServico
from sabmec.models.pessoas import Pessoa
from sabmec.models.veiculos import Veiculo
from sabmec.models.tipos import Status

os_bp = Blueprint("os", __name__)

def status_operacionais_query():
    return Status.query.filter(
        Status.situacao.ilike("PENDENTE")
        | Status.situacao.ilike("ATENDIDO")
        | Status.situacao.ilike("CANCELADO")
    ).order_by(Status.id.asc())



@os_bp.route("/ordem-de-servico")
@login_required
def os():
    pesquisar = request.args.get("pesquisar")
    busca = request.args.get("busca", "").strip()
    numero_os = request.args.get("numero_os", "").strip()
    placa = request.args.get("placa", "").strip()
    tipo_busca = request.args.get("tipo_busca", "nome")
    status_id = request.args.get("status_id", type=int)
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")

    status_lista = status_operacionais_query().all()


    if not pesquisar:
        return render_template(
            "comercial/os.html",
            ordens_servico=[],
            busca=busca,
            numero_os=numero_os,
            placa=placa,
            tipo_busca=tipo_busca,
            status_id=status_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            status_lista=status_lista,
        )

    query = (
        OrdemServico.query
        .join(Pessoa, OrdemServico.cliente_id == Pessoa.id)
        .join(Veiculo, OrdemServico.veiculo_id == Veiculo.id)
        .join(Status, OrdemServico.status_id == Status.id)
    )

    if numero_os and numero_os.isdigit():
        query = query.filter(OrdemServico.id == int(numero_os))

    if placa:
        placa_busca = placa.upper().replace("-", "").replace(" ", "")
        query = query.filter(Veiculo.placa.ilike(f"%{placa_busca}%"))

    if busca:
        busca_upper = busca.upper()

        if tipo_busca == "cpf":
            documento = "".join(filter(str.isdigit, busca))
            query = query.filter(Pessoa.documento_fiscal.ilike(f"%{documento}%"))

        elif tipo_busca == "veiculo":
            query = query.filter(
                Veiculo.modelo.ilike(f"%{busca_upper}%")
                | Veiculo.marca.ilike(f"%{busca_upper}%")
                | Veiculo.placa.ilike(f"%{busca_upper}%")
            )

        else:
            query = query.filter(Pessoa.nome.ilike(f"%{busca_upper}%"))

    if status_id:
        query = query.filter(OrdemServico.status_id == status_id)

    if data_inicio:
        query = query.filter(OrdemServico.data_abertura >= data_inicio)

    if data_fim:
        query = query.filter(OrdemServico.data_abertura <= f"{data_fim} 23:59:59")

    ordens_servico = query.order_by(OrdemServico.id.asc()).all()

    return render_template(
        "comercial/os.html",
        ordens_servico=ordens_servico,
        busca=busca,
        numero_os=numero_os,
        placa=placa,
        tipo_busca=tipo_busca,
        status_id=status_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        status_lista=status_lista,
    )


from . import os_novo, os_editar, os_faturar, os_detalhar, os_cancelar
