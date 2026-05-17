from datetime import datetime, date, time
from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func, desc

from sabmec.models.ordem_servico import OrdemServico
from sabmec.models.contas_receber import ContaReceber, ContaReceberBaixa
from sabmec.models.pessoas import Pessoa
from sabmec.models.tipos import Status


main_bp = Blueprint("main", __name__)


@main_bp.route("/home")
@login_required
def home():
    return render_template("main/home.html")


def buscar_status(nome):
    return Status.query.filter(Status.situacao.ilike(nome)).first()

def inicio_mes():
    hoje = date.today()
    return datetime(hoje.year, hoje.month, 1)

def dia_hoje():
    hoje = datetime.now()
    return hoje

@main_bp.route("/dashboard")
@login_required
def dashboard():
    from sabmec import db
    status_pendente = buscar_status("PENDENTE")
    status_atendido = buscar_status("ATENDIDO")
    status_cancelado = buscar_status("CANCELADO")

    mes_inicio = inicio_mes()
    hoje = dia_hoje()

    ordens_abertas = 0
    ordens_fechadas_mes = 0
    faturamento_mes = Decimal("0")
    cliente_top_nome = "---"
    cliente_top_total = 0

    if status_pendente:
        ordens_abertas = OrdemServico.query.filter(
            OrdemServico.status_id == status_pendente.id
        ).count()

    if status_atendido:
        ordens_fechadas_mes = OrdemServico.query.filter(
            OrdemServico.status_id == status_atendido.id,
            OrdemServico.data_abertura >= mes_inicio,
        ).count()

    faturamento_mes = (
        db.session.query(func.coalesce(func.sum(ContaReceberBaixa.valor_pago), 0))
        .join(ContaReceber, ContaReceberBaixa.conta_receber_id == ContaReceber.id)
        .filter(
            ContaReceberBaixa.data_pagamento >= mes_inicio,
            ContaReceberBaixa.data_pagamento <= hoje,
            ContaReceber.status_id == 2
        )
        .scalar()
    ) or Decimal("0")

    cliente_top = (
        OrdemServico.query
        .join(Pessoa, OrdemServico.cliente_id == Pessoa.id)
        .filter(OrdemServico.data_abertura >= mes_inicio,
                OrdemServico.status_id.in_([1, 2])
                )
        .with_entities(
            Pessoa.nome,
            func.count(OrdemServico.id).label("total_os"),
        )
        .group_by(Pessoa.id, Pessoa.nome)
        .order_by(desc("total_os"))
        .first()
    )

    if cliente_top:
        cliente_top_nome = cliente_top.nome
        cliente_top_total = cliente_top.total_os

    ultimas_ordens = (
        OrdemServico.query
        .order_by(OrdemServico.id.desc())
        .limit(8)
        .all()
    )

    contas_vencendo = (
    ContaReceber.query
    .filter(ContaReceber.status_id == 2)
    .order_by(ContaReceber.id.desc())
    .limit(6)
    .all()
    )

    return render_template(
        "main/dashboard.html",
        ordens_abertas=ordens_abertas,
        cliente_top_nome=cliente_top_nome,
        cliente_top_total=cliente_top_total,
        ordens_fechadas_mes=ordens_fechadas_mes,
        faturamento_mes=faturamento_mes,
        ultimas_ordens=ultimas_ordens,
        contas_vencendo=contas_vencendo,
        status_cancelado=status_cancelado,
    )
