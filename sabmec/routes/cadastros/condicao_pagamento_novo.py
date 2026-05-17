
from flask import render_template, redirect, url_for, flash
from sabmec.routes.cadastros.condicao_pagamento import condicao_pgto_bp
from sabmec.forms.condicao_pgto_forms import CondicaoPagamentoForm
from sabmec.models.cond_forma_pgto import FormaPagamento, CondicaoPagamento, CondicaoPagamentoParcela
from sabmec import db
from flask_login import login_required


@condicao_pgto_bp.route("/condicao/novo", methods=['GET', 'POST'])
@login_required
def condicao_pgto_novo():
    form = CondicaoPagamentoForm()
    
    # Busca as formas de pagamento ativas no banco para popular o select
    formas = FormaPagamento.query.filter_by(ativo=True).all()
    form.forma_pagamento_id.choices = [(f.id, f.nome) for f in formas]

    if form.validate_on_submit():
      
        try:
            # Instancia a nova condição
            nova_cond = CondicaoPagamento(
                nome=form.nome.data,
                forma_pagamento_id=form.forma_pagamento_id.data,
                a_vista=form.a_vista.data,
                ativo=form.ativo.data
            )
            
            dados_parcelas = form.gerar_parcelas()
            
            for p in dados_parcelas:
                parcela = CondicaoPagamentoParcela(
                    numero=p['numero'],
                    dias=p['dias'],
                    percentual=p['percentual']
                )
                nova_cond.parcelas.append(parcela)

            db.session.add(nova_cond)
            db.session.commit()
            
            return redirect(url_for('condicao.condicao_pgto'))
            
        except Exception as e:
            db.session.rollback()
            # Mostra o erro real caso algo dê errado no banco (ex: nome duplicado)
            flash(f"Erro técnico ao salvar: {str(e)}", "danger")

    # Se cair aqui (seja GET ou POST com erro), renderiza o form com os alertas
    return render_template('cadastros/condicao_pgto_novo.html', form=form)