from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date, timedelta

from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required

from sabmec import db
from sabmec.routes.comercial.os.os import os_bp
from sabmec.forms.os_forms import (
    FormOrdemServico,
    FormOrdemServicoItem,
    FormOrdemServicoPagamento,
)
from sabmec.models.pessoas import Pessoa
from sabmec.models.veiculos import Veiculo
from sabmec.models.item import Item
from sabmec.models.cond_forma_pgto import CondicaoPagamento
from sabmec.models.ordem_servico import (
    OrdemServico,
    OrdemServicoItem,
    OrdemServicoPagamento,
    OrdemServicoParcela,
)


def chave_session_itens(os_id):
    return f"os_editar_itens_{os_id}"


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


def decimal_para_dinheiro(valor):
    return Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def texto_upper(valor):
    if not valor:
        return None

    valor = valor.strip()
    return valor.upper() if valor else None


def inteiro_ou_none(valor):
    if not valor:
        return None

    try:
        return int(valor)
    except ValueError:
        return None


def carregar_choices(form_os, form_item, form_pagamento, cliente_id=None):
    if cliente_id:
        form_os.veiculo_id.choices = [(0, "Selecione...")] + [
            (veiculo.id, f"{veiculo.placa} - {veiculo.modelo}")
            for veiculo in Veiculo.query
                .filter(Veiculo.pessoa_id == cliente_id, Veiculo.ativo.is_(True))
                .order_by(Veiculo.placa)
                .all()
        ]
    else:
        form_os.veiculo_id.choices = [(0, "Selecione um cliente primeiro")]

    form_pagamento.condicao_pagamento_id.choices = [(0, "Selecione...")] + [
        (condicao.id, condicao.nome)
        for condicao in CondicaoPagamento.query
            .filter(CondicaoPagamento.ativo.is_(True))
            .order_by(CondicaoPagamento.nome)
            .all()
    ]

    form_item.item_id.choices = [(0, "Selecione...")]


def itens_da_session(os_id):
    return session.get(chave_session_itens(os_id), [])


def salvar_itens_session(os_id, itens):
    session[chave_session_itens(os_id)] = itens
    session.modified = True


def limpar_itens_session(os_id):
    session.pop(chave_session_itens(os_id), None)
    session.modified = True


def carregar_itens_os_para_session(ordem_servico):
    itens = []

    for item in ordem_servico.itens:
        itens.append({
            "item_id": item.item_id,
            "tipo": item.tipo,
            "descricao": item.descricao,
            "quantidade": str(item.quantidade),
            "valor_unitario": str(decimal_para_dinheiro(item.valor_unitario)),
            "desconto": str(decimal_para_dinheiro(item.desconto)),
            "total": str(decimal_para_dinheiro(item.total)),
        })

    salvar_itens_session(ordem_servico.id, itens)


def calcular_totais(itens, desconto_os=Decimal("0"), acrescimo_os=Decimal("0")):
    subtotal_produtos = Decimal("0")
    subtotal_servicos = Decimal("0")

    for item in itens:
        total_item = decimal_ou_zero(item.get("total"))

        if item.get("tipo") == "Produto":
            subtotal_produtos += total_item
        else:
            subtotal_servicos += total_item

    total = subtotal_produtos + subtotal_servicos - desconto_os + acrescimo_os

    return {
        "subtotal_produtos": decimal_para_dinheiro(subtotal_produtos),
        "subtotal_servicos": decimal_para_dinheiro(subtotal_servicos),
        "desconto": decimal_para_dinheiro(desconto_os),
        "acrescimo": decimal_para_dinheiro(acrescimo_os),
        "total": decimal_para_dinheiro(total),
    }


def condicao_id_atual(ordem_servico):
    condicao_id = request.form.get("condicao_pagamento_id", type=int)

    if condicao_id is not None:
        return condicao_id

    if ordem_servico.pagamento and ordem_servico.pagamento.condicao_pagamento_id:
        return ordem_servico.pagamento.condicao_pagamento_id

    return 0


def gerar_parcelas_preview(total, condicao_pagamento_id):
    parcelas = []

    if not condicao_pagamento_id or condicao_pagamento_id == 0:
        return parcelas

    condicao = CondicaoPagamento.query.get(condicao_pagamento_id)

    if not condicao:
        return parcelas

    parcelas_condicao = list(condicao.parcelas)

    if not parcelas_condicao:
        parcelas.append({
            "numero": 1,
            "vencimento": date.today(),
            "valor": decimal_para_dinheiro(total),
        })
        return parcelas

    for parcela_condicao in parcelas_condicao:
        vencimento = date.today() + timedelta(days=parcela_condicao.dias or 0)
        percentual = parcela_condicao.percentual or Decimal("0")
        valor = decimal_para_dinheiro(total * (percentual / Decimal("100")))

        parcelas.append({
            "numero": parcela_condicao.numero,
            "vencimento": vencimento,
            "valor": valor,
        })

    soma = sum((parcela["valor"] for parcela in parcelas), Decimal("0"))
    diferenca = decimal_para_dinheiro(total - soma)

    if parcelas and diferenca != 0:
        parcelas[-1]["valor"] = decimal_para_dinheiro(parcelas[-1]["valor"] + diferenca)

    return parcelas


def renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento):
    itens = itens_da_session(ordem_servico.id)

    desconto_os = decimal_ou_zero(request.form.get("desconto_os", ordem_servico.desconto))
    acrescimo_os = decimal_ou_zero(request.form.get("acrescimo_os", ordem_servico.acrescimo))

    totais = calcular_totais(itens, desconto_os, acrescimo_os)
    aba_ativa = request.form.get("aba_ativa", "dados")

    cliente_nome = ""

    if ordem_servico.cliente:
        cliente_nome = f"#{ordem_servico.cliente.id} - {ordem_servico.cliente.nome}"

        if ordem_servico.cliente.documento_fiscal:
            cliente_nome += f" ({ordem_servico.cliente.documento_fiscal})"

    condicao_pagamento_id = condicao_id_atual(ordem_servico)

    if condicao_pagamento_id:
        form_pagamento.condicao_pagamento_id.data = condicao_pagamento_id

    parcelas = gerar_parcelas_preview(totais["total"], condicao_pagamento_id)

    return render_template(
        "comercial/os_editar.html",
        ordem_servico=ordem_servico,
        form_os=form_os,
        form_item=form_item,
        form_pagamento=form_pagamento,
        itens_adicionados=itens,
        subtotal_produtos=totais["subtotal_produtos"],
        subtotal_servicos=totais["subtotal_servicos"],
        desconto=totais["desconto"],
        acrescimo=totais["acrescimo"],
        total=totais["total"],
        cliente_nome=cliente_nome,
        condicao_pagamento_id=condicao_pagamento_id,
        aba_ativa=aba_ativa,
        parcelas=parcelas,
    )


@os_bp.route("/os/<int:id>/editar", methods=["GET", "POST"])
@login_required
def os_editar(id):
    ordem_servico = OrdemServico.query.get_or_404(id)

    form_os = FormOrdemServico()
    form_item = FormOrdemServicoItem()
    form_pagamento = FormOrdemServicoPagamento()

    cliente_id = request.form.get("cliente_id", type=int) or ordem_servico.cliente_id
    carregar_choices(form_os, form_item, form_pagamento, cliente_id)

    if request.method == "GET":
        carregar_itens_os_para_session(ordem_servico)

        form_os.veiculo_id.data = ordem_servico.veiculo_id
        form_os.data_previsao.data = ordem_servico.data_previsao
        form_os.km.data = ordem_servico.km
        form_os.relato_cliente.data = ordem_servico.relato_cliente
        form_os.diagnostico.data = ordem_servico.diagnostico
        form_os.observacao.data = ordem_servico.observacao

        if ordem_servico.pagamento:
            form_pagamento.condicao_pagamento_id.data = ordem_servico.pagamento.condicao_pagamento_id

        return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

    acoes = request.form.getlist("acao")
    acao = acoes[-1] if acoes else "salvar_os"

    if acao == "adicionar_item":
        item_id = request.form.get("item_id", type=int)
        quantidade = decimal_ou_zero(request.form.get("quantidade"))
        valor_unitario = decimal_ou_zero(request.form.get("valor_unitario"))
        desconto_item = decimal_ou_zero(request.form.get("desconto_item"))

        item = Item.query.get(item_id) if item_id else None

        if not item:
            flash("Selecione um item.", "warning")
            return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

        if quantidade <= 0:
            flash("A quantidade deve ser maior que zero.", "warning")
            return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

        if valor_unitario <= 0:
            flash("O valor unitário deve ser maior que zero.", "warning")
            return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

        if desconto_item < 0:
            flash("O desconto do item não pode ser negativo.", "warning")
            return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

        total_item = (quantidade * valor_unitario) - desconto_item

        if total_item <= 0:
            flash("O total do item deve ser maior que zero.", "warning")
            return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

        itens = itens_da_session(ordem_servico.id)

        itens.append({
            "item_id": item.id,
            "tipo": item.tipo,
            "descricao": texto_upper(request.form.get("descricao")) or item.nome,
            "quantidade": str(quantidade),
            "valor_unitario": str(decimal_para_dinheiro(valor_unitario)),
            "desconto": str(decimal_para_dinheiro(desconto_item)),
            "total": str(decimal_para_dinheiro(total_item)),
        })

        salvar_itens_session(ordem_servico.id, itens)

        flash("Item adicionado.", "success")
        return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

    if acao.startswith("remover_item:"):
        indice = int(acao.split(":")[1])
        itens = itens_da_session(ordem_servico.id)

        if 0 <= indice < len(itens):
            itens.pop(indice)
            salvar_itens_session(ordem_servico.id, itens)
            flash("Item removido.", "success")

        return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

    if acao == "recalcular_pagamento":
        flash("Parcelas recalculadas.", "success")
        return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

    if acao == "salvar_os":
        try:
            itens = itens_da_session(ordem_servico.id)

            if not itens:
                flash("Não é possível gravar uma OS sem itens.", "warning")
                return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

            cliente_id = request.form.get("cliente_id", type=int)
            veiculo_id = request.form.get("veiculo_id", type=int)
            nova_condicao_id = request.form.get("condicao_pagamento_id", type=int)

            desconto_os = decimal_ou_zero(request.form.get("desconto_os"))
            acrescimo_os = decimal_ou_zero(request.form.get("acrescimo_os"))

            if not cliente_id or cliente_id == 0:
                flash("Selecione o cliente.", "warning")
                return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

            if not veiculo_id or veiculo_id == 0:
                flash("Selecione o veículo.", "warning")
                return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

            if desconto_os < 0 or acrescimo_os < 0:
                flash("Desconto e acréscimo não podem ser negativos.", "warning")
                return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

            totais = calcular_totais(itens, desconto_os, acrescimo_os)

            if totais["total"] <= 0:
                flash("Não é possível gravar uma OS com valor zerado ou negativo.", "warning")
                return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

            parcelas_preview = gerar_parcelas_preview(totais["total"], nova_condicao_id)

            if nova_condicao_id and nova_condicao_id != 0 and not parcelas_preview:
                flash("A condição de pagamento selecionada não gerou parcelas.", "warning")
                return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

            ordem_servico.cliente_id = cliente_id
            ordem_servico.veiculo_id = veiculo_id
            ordem_servico.data_previsao = form_os.data_previsao.data
            ordem_servico.km = inteiro_ou_none(request.form.get("km"))
            ordem_servico.relato_cliente = texto_upper(request.form.get("relato_cliente"))
            ordem_servico.diagnostico = texto_upper(request.form.get("diagnostico"))
            ordem_servico.observacao = texto_upper(request.form.get("observacao"))
            ordem_servico.subtotal_produtos = totais["subtotal_produtos"]
            ordem_servico.subtotal_servicos = totais["subtotal_servicos"]
            ordem_servico.desconto = totais["desconto"]
            ordem_servico.acrescimo = totais["acrescimo"]
            ordem_servico.total = totais["total"]

            OrdemServicoItem.query.filter_by(ordem_servico_id=ordem_servico.id).delete()

            for item_temp in itens:
                ordem_item = OrdemServicoItem(
                    ordem_servico_id=ordem_servico.id,
                    item_id=item_temp["item_id"],
                    tipo=item_temp["tipo"],
                    descricao=item_temp["descricao"],
                    quantidade=decimal_ou_zero(item_temp["quantidade"]),
                    valor_unitario=decimal_ou_zero(item_temp["valor_unitario"]),
                    desconto=decimal_ou_zero(item_temp["desconto"]),
                    total=decimal_ou_zero(item_temp["total"]),
                )

                db.session.add(ordem_item)

            OrdemServicoParcela.query.filter_by(
                ordem_servico_id=ordem_servico.id
            ).delete()

            OrdemServicoPagamento.query.filter_by(
                ordem_servico_id=ordem_servico.id
            ).delete()

            db.session.flush()

            if nova_condicao_id and nova_condicao_id != 0:
                condicao = CondicaoPagamento.query.get(nova_condicao_id)

                pagamento = OrdemServicoPagamento(
                    ordem_servico_id=ordem_servico.id,
                    condicao_pagamento_id=condicao.id,
                    nome_condicao=condicao.nome,
                    valor_total=ordem_servico.total,
                    quantidade_parcelas=len(parcelas_preview) or 1,
                )

                db.session.add(pagamento)
                db.session.flush()

                for parcela_preview in parcelas_preview:
                    parcela = OrdemServicoParcela(
                        ordem_servico_id=ordem_servico.id,
                        numero=parcela_preview["numero"],
                        vencimento=parcela_preview["vencimento"],
                        valor=parcela_preview["valor"],
                    )

                    db.session.add(parcela)

            db.session.commit()
            limpar_itens_session(ordem_servico.id)

            flash("OS atualizada com sucesso.", "success")
            return redirect(url_for("os.os"))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao atualizar OS: {erro}", "danger")

    return renderizar_os_editar(ordem_servico, form_os, form_item, form_pagamento)

