from datetime import date
from decimal import Decimal, InvalidOperation

from flask import redirect, url_for, flash, request
from flask_login import login_required

from sabmec import db
from sabmec.routes.financeiro.contas_receber import contas_receber_bp
from sabmec.models.contas_receber import ContaReceber, ContaReceberBaixa
from sabmec.models.tipos import Status


def decimal_ou_zero(valor):
    if valor in [None, ""]:
        return Decimal("0")

    valor = str(valor).strip()

    try:
        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")

        return Decimal(valor)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def buscar_status(nome):
    return Status.query.filter(Status.situacao.ilike(nome)).first()


@contas_receber_bp.route("/contas-receber/<int:id>/baixar", methods=["POST"])
@login_required
def contas_receber_baixar(id):
    conta = ContaReceber.query.get_or_404(id)

    try:
        situacao = conta.status_situacao.strip().lower() if conta.status_situacao else ""

        if situacao in ["cancelado", "cancelada"]:
            flash("Não é possível baixar uma conta cancelada.", "warning")
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        if situacao in ["atendido", "atendida", "pago", "paga"]:
            flash("Essa conta já está baixada.", "warning")
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        data_pagamento = request.form.get("data_pagamento")
        valor_pago = decimal_ou_zero(request.form.get("valor_pago"))
        juros = decimal_ou_zero(request.form.get("juros"))
        multa = decimal_ou_zero(request.form.get("multa"))
        desconto = decimal_ou_zero(request.form.get("desconto"))
        observacao = request.form.get("observacao")

        if not data_pagamento:
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        if valor_pago <= 0:
            flash("O valor pago deve ser maior que zero.", "warning")
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        if juros < 0 or multa < 0 or desconto < 0:
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        valor_restante_atual = conta.valor_restante or Decimal("0")

        if valor_pago > valor_restante_atual:
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        baixa = ContaReceberBaixa(
            conta_receber_id=conta.id,
            data_pagamento=date.fromisoformat(data_pagamento),
            valor_pago=valor_pago,
            juros=juros,
            multa=multa,
            desconto=desconto,
            observacao=observacao.strip().upper() if observacao else None,
        )

        db.session.add(baixa)

        novo_restante = valor_restante_atual - valor_pago

        if novo_restante <= 0:
            status_atendido = buscar_status("ATENDIDO")

            if not status_atendido:
                db.session.rollback()
                return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

            conta.status_id = status_atendido.id

        else:
            status_parcial = buscar_status("PARCIAL")

            if status_parcial:
                conta.status_id = status_parcial.id

        db.session.commit()

        return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao baixar conta: {erro}", "danger")
        return redirect(url_for("contas_receber.contas_receber", pesquisar=1))
