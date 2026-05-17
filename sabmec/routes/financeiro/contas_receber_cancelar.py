from flask import redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.financeiro.contas_receber import contas_receber_bp
from sabmec.models.contas_receber import ContaReceber
from sabmec.models.tipos import Status


def buscar_status(nome):
    return Status.query.filter(Status.situacao.ilike(nome)).first()


def situacao_conta(conta):
    if not conta.status:
        return ""

    return (conta.status.situacao or "").strip().lower()


@contas_receber_bp.route("/contas-receber/<int:id>/cancelar", methods=["POST"])
@login_required
def contas_receber_cancelar(id):
    conta = ContaReceber.query.get_or_404(id)

    try:
        situacao = situacao_conta(conta)

        if situacao in ["cancelado", "cancelada"]:
            flash("Essa conta já está cancelada.", "warning")
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        if situacao != "pendente":
            flash("Somente contas pendentes podem ser canceladas.", "warning")
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        status_cancelado = buscar_status("CANCELADO")

        if not status_cancelado:
            flash("Cadastre o status CANCELADO antes de cancelar contas.", "danger")
            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        conta.status_id = status_cancelado.id

        db.session.commit()

        return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao cancelar conta: {erro}", "danger")
        return redirect(url_for("contas_receber.contas_receber", pesquisar=1))
