from datetime import date

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.models.contas_pagar import ContaPagar
from sabmec.routes.financeiro.contas_pagar import contas_pagar_bp


def texto_upper(valor):
    if not valor:
        return None

    valor = valor.strip()
    return valor.upper() if valor else None


@contas_pagar_bp.route("/contas-pagar/<int:id>/editar", methods=["GET", "POST"])
@login_required
def contas_pagar_editar(id):
    conta = ContaPagar.query.get_or_404(id)

    if request.method == "POST":
        try:
            descricao = texto_upper(request.form.get("descricao"))
            parcela = texto_upper(request.form.get("parcela"))
            documento = texto_upper(request.form.get("documento"))
            vencimento = request.form.get("vencimento")
            observacao = texto_upper(request.form.get("observacao"))

            if not descricao:
                flash("Informe a descricao.", "warning")
                return render_template("financeiro/contas_pagar_editar.html", conta=conta)

            if not vencimento:
                flash("Informe o vencimento.", "warning")
                return render_template("financeiro/contas_pagar_editar.html", conta=conta)

            conta.descricao = descricao
            conta.parcela = parcela
            conta.documento = documento
            conta.vencimento = date.fromisoformat(vencimento)
            conta.observacao = observacao

            db.session.commit()

            return redirect(url_for("contas_pagar.contas_pagar", pesquisar=1))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao atualizar conta a pagar: {erro}", "danger")

    return render_template(
        "financeiro/contas_pagar_editar.html",
        conta=conta,
    )
