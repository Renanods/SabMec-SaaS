from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date, timedelta
from flask_login import login_required
from flask import render_template, request, redirect, url_for, flash, jsonify, session

from sabmec import db
from sabmec.routes.comercial.os import os_bp
from sabmec.forms.os_forms import (
    FormOrdemServico,
    FormOrdemServicoItem,
    FormOrdemServicoPagamento,
)
from sabmec.models.pessoas import Pessoa
from sabmec.models.veiculos import Veiculo
from sabmec.models.item import Item
from sabmec.models.tipos import Status
from sabmec.models.cond_forma_pgto import CondicaoPagamento
from sabmec.models.ordem_servico import (
    OrdemServico,
    OrdemServicoItem,
    OrdemServicoPagamento,
    OrdemServicoParcela,
)


SESSION_OS_ITENS = "os_novo_itens"


def decimal_ou_zero(valor):
    if valor in [None, ""]:
        return Decimal("0")

    try:
        return Decimal(str(valor).replace(",", "."))
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


def status_padrao_os():
    status = Status.query.filter(Status.situacao.ilike("PENDENTE")).first()

    if status:
        return status

    return Status.query.order_by(Status.id.asc()).first()


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


def itens_da_session():
    return session.get(SESSION_OS_ITENS, [])


def salvar_itens_session(itens):
    session[SESSION_OS_ITENS] = itens
    session.modified = True


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


def renderizar_os_novo(form_os, form_item, form_pagamento):
    itens = itens_da_session()
    desconto_os = decimal_ou_zero(request.form.get("desconto_os"))
    acrescimo_os = decimal_ou_zero(request.form.get("acrescimo_os"))
    totais = calcular_totais(itens, desconto_os, acrescimo_os)
    aba_ativa = request.form.get("aba_ativa", "dados")

    cliente_id = request.form.get("cliente_id", type=int)
    cliente_nome = ""

    if cliente_id:
        cliente = Pessoa.query.get(cliente_id)
        if cliente:
            cliente_nome = f"#{cliente.id} - {cliente.nome}"
            if cliente.documento_fiscal:
                cliente_nome += f" ({cliente.documento_fiscal})"

    return render_template(
        "comercial/os_novo.html",
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
        aba_ativa=aba_ativa,
    )


@os_bp.route("/os/novo", methods=["GET", "POST"])
@login_required
def os_novo():
    form_os = FormOrdemServico()
    form_item = FormOrdemServicoItem()
    form_pagamento = FormOrdemServicoPagamento()

    cliente_id = request.form.get("cliente_id", type=int)
    carregar_choices(form_os, form_item, form_pagamento, cliente_id)

    if request.method == "GET":
        salvar_itens_session([])
        return renderizar_os_novo(form_os, form_item, form_pagamento)

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
            return renderizar_os_novo(form_os, form_item, form_pagamento)

        if quantidade <= 0:
            flash("A quantidade deve ser maior que zero.", "warning")
            return renderizar_os_novo(form_os, form_item, form_pagamento)

        if valor_unitario <= 0:
            flash("O valor unitário deve ser maior que zero.", "warning")
            return renderizar_os_novo(form_os, form_item, form_pagamento)

        if desconto_item < 0:
            flash("O desconto do item não pode ser negativo.", "warning")
            return renderizar_os_novo(form_os, form_item, form_pagamento)

        subtotal = quantidade * valor_unitario
        total_item = subtotal - desconto_item

        if total_item <= 0:
            flash("O total do item deve ser maior que zero.", "warning")
            return renderizar_os_novo(form_os, form_item, form_pagamento)

        itens = itens_da_session()
        itens.append({
            "item_id": item.id,
            "tipo": item.tipo,
            "descricao": texto_upper(request.form.get("descricao")) or item.nome,
            "quantidade": str(quantidade),
            "valor_unitario": str(decimal_para_dinheiro(valor_unitario)),
            "desconto": str(decimal_para_dinheiro(desconto_item)),
            "total": str(decimal_para_dinheiro(total_item)),
        })

        salvar_itens_session(itens)

        flash("Item adicionado.", "success")
        return renderizar_os_novo(form_os, form_item, form_pagamento)

    if acao.startswith("remover_item:"):
        indice = int(acao.split(":")[1])
        itens = itens_da_session()

        if 0 <= indice < len(itens):
            itens.pop(indice)
            salvar_itens_session(itens)
            flash("Item removido.", "success")

        return renderizar_os_novo(form_os, form_item, form_pagamento)

    if acao == "salvar_os":
        try:
            itens = itens_da_session()

            if not itens:
                flash("Não é possível gravar uma ordem de serviço sem itens.", "warning")
                return renderizar_os_novo(form_os, form_item, form_pagamento)

            cliente_id = request.form.get("cliente_id", type=int)
            veiculo_id = request.form.get("veiculo_id", type=int)
            condicao_pagamento_id = request.form.get("condicao_pagamento_id", type=int)

            desconto_os = decimal_ou_zero(request.form.get("desconto_os"))
            acrescimo_os = decimal_ou_zero(request.form.get("acrescimo_os"))

            if not cliente_id or cliente_id == 0:
                flash("Selecione o cliente.", "warning")
                return renderizar_os_novo(form_os, form_item, form_pagamento)

            if not veiculo_id or veiculo_id == 0:
                flash("Selecione o veículo.", "warning")
                return renderizar_os_novo(form_os, form_item, form_pagamento)

            status = status_padrao_os()

            if not status:
                flash("Nenhum status padrão encontrado para abrir a OS.", "danger")
                return renderizar_os_novo(form_os, form_item, form_pagamento)

            if desconto_os < 0 or acrescimo_os < 0:
                flash("Desconto e acréscimo não podem ser negativos.", "warning")
                return renderizar_os_novo(form_os, form_item, form_pagamento)

            totais = calcular_totais(itens, desconto_os, acrescimo_os)

            if totais["total"] <= 0:
                flash("Não é possível gravar uma OS com valor zerado ou negativo.", "warning")
                return renderizar_os_novo(form_os, form_item, form_pagamento)

            ordem_servico = OrdemServico(
                cliente_id=cliente_id,
                veiculo_id=veiculo_id,
                status_id=status.id,
                data_previsao=form_os.data_previsao.data,
                km=inteiro_ou_none(request.form.get("km")),
                relato_cliente=texto_upper(request.form.get("relato_cliente")),
                diagnostico=texto_upper(request.form.get("diagnostico")),
                observacao=texto_upper(request.form.get("observacao")),
                subtotal_produtos=totais["subtotal_produtos"],
                subtotal_servicos=totais["subtotal_servicos"],
                desconto=totais["desconto"],
                acrescimo=totais["acrescimo"],
                total=totais["total"],
            )

            db.session.add(ordem_servico)
            db.session.flush()

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

            if condicao_pagamento_id and condicao_pagamento_id != 0:
                condicao = CondicaoPagamento.query.get(condicao_pagamento_id)

                if condicao:
                    pagamento = OrdemServicoPagamento(
                        ordem_servico_id=ordem_servico.id,
                        condicao_pagamento_id=condicao.id,
                        nome_condicao=condicao.nome,
                        valor_total=ordem_servico.total,
                        quantidade_parcelas=len(condicao.parcelas) or 1,
                    )

                    db.session.add(pagamento)
                    db.session.flush()

                    for parcela_condicao in condicao.parcelas:
                        vencimento = date.today() + timedelta(days=parcela_condicao.dias)
                        valor = decimal_para_dinheiro(
                            ordem_servico.total * (parcela_condicao.percentual / Decimal("100"))
                        )

                        parcela = OrdemServicoParcela(
                            ordem_servico_id=ordem_servico.id,
                            numero=parcela_condicao.numero,
                            vencimento=vencimento,
                            valor=valor,
                        )

                        db.session.add(parcela)

            db.session.commit()
            salvar_itens_session([])

            
            return redirect(url_for("os.os"))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao cadastrar OS: {erro}", "danger")

    return renderizar_os_novo(form_os, form_item, form_pagamento)


@os_bp.route("/os/buscar-clientes")
def buscar_clientes():
    termo = request.args.get("q", "").strip().upper()
    tipo_busca = request.args.get("tipo_busca", "nome")

    query = Pessoa.query.filter(
        Pessoa.ativo.is_(True),
        Pessoa.eh_cliente.is_(True),
    )

    if termo:
        if tipo_busca == "id" and termo.isdigit():
            query = query.filter(Pessoa.id == int(termo))

        elif tipo_busca == "documento":
            documento = "".join(filter(str.isdigit, termo))
            query = query.filter(Pessoa.documento_fiscal.ilike(f"%{documento}%"))

        else:
            query = query.filter(Pessoa.nome.ilike(f"%{termo}%"))

    clientes = query.order_by(Pessoa.id.asc()).limit(50).all()

    return jsonify({
        "clientes": [
            {
                "id": cliente.id,
                "nome": cliente.nome,
                "documento": cliente.documento_fiscal,
            }
            for cliente in clientes
        ]
    })


@os_bp.route("/os/buscar-itens")
def buscar_itens():
    termo = request.args.get("q", "").strip().upper()
    tipo_busca = request.args.get("tipo_busca", "nome")

    query = Item.query.filter(Item.ativo.is_(True))

    if termo:
        if tipo_busca == "id" and termo.isdigit():
            query = query.filter(Item.id == int(termo))
        else:
            query = query.filter(Item.nome.ilike(f"%{termo}%"))

    itens = query.order_by(Item.id.asc()).limit(50).all()

    return jsonify({
        "itens": [
            {
                "id": item.id,
                "nome": item.nome,
                "tipo": item.tipo,
                "preco": str(item.preco).replace(".", ","),
            }
            for item in itens
        ]
    })


@os_bp.route("/os/veiculos-por-cliente/<int:cliente_id>")
def veiculos_por_cliente(cliente_id):
    veiculos = Veiculo.query.filter_by(
        pessoa_id=cliente_id,
        ativo=True,
    ).order_by(Veiculo.placa).all()

    return jsonify({
        "veiculos": [
            {
                "id": veiculo.id,
                "placa": veiculo.placa,
                "modelo": veiculo.modelo,
            }
            for veiculo in veiculos
        ]
    })


@os_bp.route("/os/item/<int:item_id>")
def item_por_id(item_id):
    item = Item.query.get_or_404(item_id)

    return jsonify({
        "id": item.id,
        "nome": item.nome,
        "tipo": item.tipo,
        "preco": str(item.preco).replace(".", ","),
    })
