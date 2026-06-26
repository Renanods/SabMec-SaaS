from flask import redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.models.contas_pagar import ContaPagar
from sabmec.models.tipos import Status
from sabmec.routes.financeiro.contas_pagar import contas_pagar_bp


def buscar_status(nome):
    return Status.query.filter(Status.situacao.ilike(nome)).first()


def situacao_conta(conta):
    if not conta.status:
        return ""

    return (conta.status.situacao or "").strip().lower()


@contas_pagar_bp.route("/contas-pagar/<int:id>/cancelar", methods=["POST"])
@login_required
def contas_pagar_cancelar(id):
    conta = ContaPagar.query.get_or_404(id)

    try:
        situacao = situacao_conta(conta)

        if situacao in ["cancelado", "cancelada"]:
            flash("Essa conta ja esta cancelada.", "warning")
            return redirect(url_for("contas_pagar.contas_pagar", pesquisar=1))

        if situacao != "pendente":
            flash("Somente contas pendentes podem ser canceladas.", "warning")
            return redirect(url_for("contas_pagar.contas_pagar", pesquisar=1))

        status_cancelado = buscar_status("CANCELADO")

        if not status_cancelado:
            flash("Cadastre o status CANCELADO antes de cancelar contas.", "danger")
            return redirect(url_for("contas_pagar.contas_pagar", pesquisar=1))

        conta.status_id = status_cancelado.id

        db.session.commit()

        return redirect(url_for("contas_pagar.contas_pagar", pesquisar=1))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao cancelar conta: {erro}", "danger")
        return redirect(url_for("contas_pagar.contas_pagar", pesquisar=1))
