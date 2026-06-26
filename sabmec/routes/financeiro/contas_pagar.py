from datetime import date

from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_

from sabmec.models.contas_pagar import ContaPagar
from sabmec.models.pessoas import Pessoa
from sabmec.models.tipos import Status


contas_pagar_bp = Blueprint("contas_pagar", __name__)


def status_operacionais_query():
    return Status.query.filter(
        Status.situacao.ilike("PENDENTE")
        | Status.situacao.ilike("ATENDIDO")
        | Status.situacao.ilike("CANCELADO")
    ).order_by(Status.id.asc())


@contas_pagar_bp.route("/contas-pagar")
@login_required
def contas_pagar():
    pesquisar = request.args.get("pesquisar")
    busca = request.args.get("busca", "").strip()
    tipo_busca = request.args.get("tipo_busca", "fornecedor")
    status_id = request.args.get("status_id", type=int)
    origem = request.args.get("origem", "")
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")

    status_lista = status_operacionais_query().all()
    contas = []

    if pesquisar:
        query = (
            ContaPagar.query
            .join(Pessoa, ContaPagar.fornecedor_id == Pessoa.id)
            .join(Status, ContaPagar.status_id == Status.id)
        )

        if origem:
            query = query.filter(ContaPagar.origem == origem)

        if busca:
            busca_upper = busca.upper()
            busca_numeros = "".join(filter(str.isdigit, busca))

            if tipo_busca == "fornecedor":
                query = query.filter(Pessoa.nome.ilike(f"%{busca_upper}%"))

            elif tipo_busca == "descricao":
                query = query.filter(ContaPagar.descricao.ilike(f"%{busca_upper}%"))

            elif tipo_busca == "documento":
                query = query.filter(ContaPagar.documento.ilike(f"%{busca_upper}%"))

            elif tipo_busca == "cpf_cnpj":
                if busca_numeros:
                    query = query.filter(Pessoa.documento_fiscal.ilike(f"%{busca_numeros}%"))
                else:
                    query = query.filter(False)

            else:
                query = query.filter(
                    or_(
                        Pessoa.nome.ilike(f"%{busca_upper}%"),
                        ContaPagar.descricao.ilike(f"%{busca_upper}%"),
                        ContaPagar.documento.ilike(f"%{busca_upper}%"),
                        ContaPagar.origem.ilike(f"%{busca_upper}%"),
                    )
                )

        if status_id:
            query = query.filter(ContaPagar.status_id == status_id)

        if data_inicio:
            query = query.filter(ContaPagar.vencimento >= data_inicio)

        if data_fim:
            query = query.filter(ContaPagar.vencimento <= data_fim)

        contas = query.order_by(
            ContaPagar.id.asc(),
        ).all()

    return render_template(
        "financeiro/contas_pagar.html",
        contas_pagar=contas,
        busca=busca,
        tipo_busca=tipo_busca,
        status_id=status_id,
        origem=origem,
        data_inicio=data_inicio,
        data_fim=data_fim,
        status_lista=status_lista,
        hoje=date.today().isoformat(),
    )


from sabmec.routes.financeiro.contas_pagar_baixar import contas_pagar_baixar
from sabmec.routes.financeiro.contas_pagar_cancelar import contas_pagar_cancelar
from sabmec.routes.financeiro.contas_pagar_editar import contas_pagar_editar
from sabmec.routes.financeiro.contas_pagar_estornar import contas_pagar_estornar
from sabmec.routes.financeiro.contas_pagar_novo import contas_pagar_novo
