from datetime import date

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.financeiro.contas_receber import contas_receber_bp
from sabmec.models.contas_receber import ContaReceber


def texto_upper(valor):
    if not valor:
        return None

    valor = valor.strip()
    return valor.upper() if valor else None


@contas_receber_bp.route("/contas-receber/<int:id>/editar", methods=["GET", "POST"])
@login_required
def contas_receber_editar(id):
    conta = ContaReceber.query.get_or_404(id)

    if request.method == "POST":
        try:
            descricao = texto_upper(request.form.get("descricao"))
            parcela = texto_upper(request.form.get("parcela"))
            vencimento = request.form.get("vencimento")
            referencia_id = request.form.get("referencia_id", type=int)
            observacao = texto_upper(request.form.get("observacao"))

            if not descricao:
                flash("Informe a descrição.", "warning")
                return render_template("financeiro/contas_receber_editar.html", conta=conta)

            if not vencimento:
                flash("Informe o vencimento.", "warning")
                return render_template("financeiro/contas_receber_editar.html", conta=conta)

            conta.descricao = descricao
            conta.parcela = parcela
            conta.vencimento = date.fromisoformat(vencimento)
            conta.referencia_id = referencia_id
            conta.observacao = observacao

            db.session.commit()

            return redirect(url_for("contas_receber.contas_receber", pesquisar=1))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao atualizar conta a receber: {erro}", "danger")

    return render_template(
        "financeiro/contas_receber_editar.html",
        conta=conta,
    )
