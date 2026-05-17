from decimal import Decimal, InvalidOperation

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.cadastros.condicao_pagamento import condicao_pgto_bp
from sabmec.models.cond_forma_pgto import CondicaoPagamento, CondicaoPagamentoParcela


def texto_upper(valor):
    if not valor:
        return None

    valor = valor.strip()
    return valor.upper() if valor else None


def inteiro_ou_zero(valor):
    if not valor:
        return 0

    try:
        return int(valor)
    except ValueError:
        return 0


def decimal_ou_none(valor):
    if valor in [None, ""]:
        return None

    try:
        return Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def renderizar_edicao(condicao):
    return render_template(
        "cadastros/condicao_pgto_editar.html",
        condicao=condicao,
    )


@condicao_pgto_bp.route("/condicao/<int:id>/editar", methods=["GET", "POST"])
@login_required
def condicoes_pagamento_editar(id):
    condicao = CondicaoPagamento.query.get_or_404(id)

    if request.method == "POST":
        try:
            nome = texto_upper(request.form.get("nome"))
            descricao = texto_upper(request.form.get("descricao"))
            ativo = True if request.form.get("ativo") else False

            numeros = request.form.getlist("parcela_numero[]")
            dias_lista = request.form.getlist("parcela_dias[]")
            percentuais = request.form.getlist("parcela_percentual[]")

            if not nome:
                flash("Informe o nome da condição de pagamento.", "warning")
                return renderizar_edicao(condicao)

            if not numeros:
                flash("Informe pelo menos uma parcela.", "warning")
                return renderizar_edicao(condicao)

            parcelas_temp = []
            soma_percentual = Decimal("0")

            for indice in range(len(numeros)):
                numero = inteiro_ou_zero(numeros[indice])
                dias = inteiro_ou_zero(dias_lista[indice]) if indice < len(dias_lista) else 0
                percentual = decimal_ou_none(percentuais[indice]) if indice < len(percentuais) else None

                if numero <= 0:
                    flash("O número da parcela deve ser maior que zero.", "warning")
                    return renderizar_edicao(condicao)

                if dias < 0:
                    flash("Os dias da parcela não podem ser negativos.", "warning")
                    return renderizar_edicao(condicao)

                if percentual is None or percentual <= 0:
                    flash("O percentual da parcela deve ser maior que zero.", "warning")
                    return renderizar_edicao(condicao)

                soma_percentual += percentual

                parcelas_temp.append({
                    "numero": numero,
                    "dias": dias,
                    "percentual": percentual,
                })

            if soma_percentual != Decimal("100"):
                flash("A soma dos percentuais das parcelas deve ser exatamente 100%.", "warning")
                return renderizar_edicao(condicao)

            condicao.nome = nome
            condicao.descricao = descricao
            condicao.ativo = ativo

            CondicaoPagamentoParcela.query.filter_by(condicao_id=condicao.id).delete()

            parcelas_temp.sort(key=lambda parcela: parcela["numero"])

            for parcela_temp in parcelas_temp:
                parcela = CondicaoPagamentoParcela(
                    condicao_id=condicao.id,
                    numero=parcela_temp["numero"],
                    dias=parcela_temp["dias"],
                    percentual=parcela_temp["percentual"],
                )

                db.session.add(parcela)

            db.session.commit()

            flash("Condição de pagamento atualizada com sucesso.", "success")
            return redirect(url_for("condicao.condicao_pgto"))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao atualizar condição de pagamento: {erro}", "danger")

    return renderizar_edicao(condicao)
