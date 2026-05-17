from flask import redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.financeiro.contas_receber import contas_receber_bp
from sabmec.models.contas_receber import ContaReceber, ContaReceberBaixa
from sabmec.models.tipos import Status


def buscar_status(nome):
    return Status.query.filter(Status.situacao.ilike(nome)).first()


def situacao_conta(conta):
    if not conta.status:
        return ""

    return (conta.status.situacao or "").strip().lower()


@contas_receber_bp.route("/contas-receber/<int:id>/estornar", methods=["POST"])
@login_required
def contas_receber_estornar(id):
    conta = ContaReceber.query.get_or_404(id)

    try:
        situacao = situacao_conta(conta)

        if situacao not in ["atendido", "atendida", "pago", "paga"]:
            flash("Somente contas atendidas/pagas podem ser estornadas.", "warning")
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        status_pendente = buscar_status("PENDENTE")

        if not status_pendente:
            flash("Cadastre o status PENDENTE antes de estornar contas.", "danger")
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        ContaReceberBaixa.query.filter_by(
            conta_receber_id=conta.id,
        ).delete()

        conta.status_id = status_pendente.id

        db.session.commit()

        return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao estornar conta: {erro}", "danger")
        return redirect(url_for("contas_receber.contas_receber", pesquisar=1))
