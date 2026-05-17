from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_
from datetime import date

from sabmec.models.contas_receber import ContaReceber
from sabmec.models.pessoas import Pessoa
from sabmec.models.tipos import Status


contas_receber_bp = Blueprint("contas_receber", __name__)


def status_operacionais_query():
    return Status.query.filter(
        Status.situacao.ilike("PENDENTE")
        | Status.situacao.ilike("ATENDIDO")
        | Status.situacao.ilike("CANCELADO")
    ).order_by(Status.id.asc())


@contas_receber_bp.route("/contas-receber")
@login_required
def contas_receber():
    pesquisar = request.args.get("pesquisar")
    busca = request.args.get("busca", "").strip()
    tipo_busca = request.args.get("tipo_busca", "cliente")
    status_id = request.args.get("status_id", type=int)
    origem = request.args.get("origem", "")
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")

    status_lista = status_operacionais_query().all()
    contas = []

    if pesquisar:
        query = (
            ContaReceber.query
            .join(Pessoa, ContaReceber.cliente_id == Pessoa.id)
            .join(Status, ContaReceber.status_id == Status.id)
        )

        if origem:
            query = query.filter(ContaReceber.origem == origem)

        if busca:
            busca_upper = busca.upper()
            busca_numeros = "".join(filter(str.isdigit, busca))

            if tipo_busca == "cliente":
                query = query.filter(Pessoa.nome.ilike(f"%{busca_upper}%"))

            elif tipo_busca == "descricao":
                query = query.filter(ContaReceber.descricao.ilike(f"%{busca_upper}%"))

            elif tipo_busca == "referencia":
                if busca.isdigit():
                    query = query.filter(
                        or_(
                            ContaReceber.id == int(busca),
                            ContaReceber.referencia_id == int(busca),
                        )
                    )
                else:
                    query = query.filter(False)

            elif tipo_busca == "documento":
                if busca_numeros:
                    query = query.filter(Pessoa.documento_fiscal.ilike(f"%{busca_numeros}%"))
                else:
                    query = query.filter(False)

            else:
                query = query.filter(
                    or_(
                        Pessoa.nome.ilike(f"%{busca_upper}%"),
                        ContaReceber.descricao.ilike(f"%{busca_upper}%"),
                        ContaReceber.origem.ilike(f"%{busca_upper}%"),
                    )
                )

        if status_id:
            query = query.filter(ContaReceber.status_id == status_id)

        if data_inicio:
            query = query.filter(ContaReceber.vencimento >= data_inicio)

        if data_fim:
            query = query.filter(ContaReceber.vencimento <= data_fim)

        contas = query.order_by(
            # ContaReceber.vencimento.asc(),
            ContaReceber.id.asc(),
        ).all()

    return render_template(
        "financeiro/contas_receber.html",
        contas_receber=contas,
        busca=busca,
        tipo_busca=tipo_busca,
        status_id=status_id,
        origem=origem,
        data_inicio=data_inicio,
        data_fim=data_fim,
        status_lista=status_lista,
        hoje=date.today().isoformat(),

    )

from sabmec.routes.financeiro.contas_receber_baixar import contas_receber_baixar
from sabmec.routes.financeiro.contas_receber_novo import contas_receber_novo
from sabmec.routes.financeiro.contas_receber_editar import contas_receber_editar
from sabmec.routes.financeiro.contas_receber_estornar import contas_receber_estornar
from sabmec.routes.financeiro.contas_receber_cancelar import contas_receber_cancelar