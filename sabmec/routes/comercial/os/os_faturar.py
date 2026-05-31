from flask import redirect, url_for, flash
from flask_login import login_required

from datetime import datetime

from sabmec import db
from sabmec.routes.comercial.os.os import os_bp
from sabmec.models.tipos import Status
from sabmec.models.ordem_servico import OrdemServico
from sabmec.models.contas_receber import ContaReceber, ContaReceberBaixa


def buscar_status(nome):
    return Status.query.filter(Status.situacao.ilike(nome)).first()


def dia_hoje():
    return datetime.now()


def debitar_estoque(ordem_servico):
    for ordem_item in ordem_servico.itens:
        if ordem_item.tipo != "Produto":
            continue

        if not ordem_item.item or not ordem_item.item.mercadoria:
            continue

        quantidade = float(ordem_item.quantidade or 0)
        ordem_item.item.mercadoria.estoque = (ordem_item.item.mercadoria.estoque or 0) - quantidade


@os_bp.route("/os/<int:id>/faturar", methods=["POST"])
@login_required
def os_faturar(id):
    ordem_servico = OrdemServico.query.get_or_404(id)
    hoje = dia_hoje()

    try:
        if not ordem_servico.itens:
            flash("Não é possível faturar uma OS sem itens.", "warning")
            return redirect(url_for("os.os"))

        if not ordem_servico.total or ordem_servico.total <= 0:
            flash("Não é possível faturar uma OS com valor zerado ou negativo.", "warning")
            return redirect(url_for("os.os"))

        conta_existente = ContaReceber.query.filter_by(
            origem="OS",
            referencia_id=ordem_servico.id,
        ).first()

        if conta_existente:
            flash("Essa OS já foi faturada.", "warning")
            return redirect(url_for("os.os"))

        status_pendente = buscar_status("PENDENTE")
        status_atendido = buscar_status("ATENDIDO")

        if not status_pendente:
            flash("Cadastre o status PENDENTE antes de faturar.", "danger")
            return redirect(url_for("os.os"))

        if not status_atendido:
            flash("Cadastre o status ATENDIDO antes de faturar.", "danger")
            return redirect(url_for("os.os"))

        debitar_estoque(ordem_servico)

        eh_avista = False

        if ordem_servico.pagamento and ordem_servico.pagamento.condicao_pagamento:
            eh_avista = ordem_servico.pagamento.condicao_pagamento.a_vista

        if eh_avista:
            conta = ContaReceber(
                cliente_id=ordem_servico.cliente_id,
                status_id=status_atendido.id,
                origem="OS",
                referencia_id=ordem_servico.id,
                descricao=f"OS #{ordem_servico.id} (À Vista)",
                parcela="1/1",
                valor=ordem_servico.total,
                vencimento=hoje.date(),
                observacao=f"Gerado pelo faturamento da OS #{ordem_servico.id}",
            )

            db.session.add(conta)
            db.session.flush()

            baixa = ContaReceberBaixa(
                conta_receber_id=conta.id,
                data_pagamento=hoje.date(),
                valor_pago=ordem_servico.total,
                observacao="Recebimento automático via faturamento à vista.",
            )

            db.session.add(baixa)

        else:
            parcelas = []

            if ordem_servico.pagamento and ordem_servico.pagamento.parcelas:
                parcelas = ordem_servico.pagamento.parcelas

            if parcelas:
                quantidade_parcelas = len(parcelas)

                for parcela in parcelas:
                    conta = ContaReceber(
                        cliente_id=ordem_servico.cliente_id,
                        status_id=status_pendente.id,
                        origem="OS",
                        referencia_id=ordem_servico.id,
                        descricao=f"OS #{ordem_servico.id}",
                        parcela=f"{parcela.numero}/{quantidade_parcelas}",
                        valor=parcela.valor,
                        vencimento=parcela.vencimento,
                        observacao=f"Gerado pelo faturamento da OS #{ordem_servico.id}",
                    )

                    db.session.add(conta)

            else:
                conta = ContaReceber(
                    cliente_id=ordem_servico.cliente_id,
                    status_id=status_pendente.id,
                    origem="OS",
                    referencia_id=ordem_servico.id,
                    descricao=f"OS #{ordem_servico.id}",
                    parcela="1/1",
                    valor=ordem_servico.total,
                    vencimento=hoje.date(),
                    observacao=f"Gerado pelo faturamento da OS #{ordem_servico.id}",
                )

                db.session.add(conta)

        ordem_servico.status_id = status_atendido.id

        db.session.commit()

        return redirect(url_for("os.os"))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao faturar OS: {erro}", "danger")
        return redirect(url_for("os.os"))
