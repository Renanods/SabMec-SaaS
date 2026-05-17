
from flask import Blueprint, render_template, request
from sabmec.models.cond_forma_pgto import CondicaoPagamento
from flask_login import login_required
condicao_pgto_bp = Blueprint("condicao", __name__)


@condicao_pgto_bp.route("/condicao")
@login_required
def condicao_pgto():
    pesquisar  = request.args.get('pesquisar')
    busca      = request.args.get('busca', '').strip()
    status     = request.args.get('status', '')
    tipo_busca = request.args.get('tipo_busca', 'codigo')

    condicoes = []

    if pesquisar:
        query = CondicaoPagamento.query

        # Filtro de status
        if status == 'ativo':
            query = query.filter_by(ativo=True)
        elif status == 'inativo':
            query = query.filter_by(ativo=False)

        # Filtro de busca
        if busca:
            if tipo_busca == 'codigo':
                # Busca pelo id, ignora texto que não seja número
                if busca.isdigit():
                    query = query.filter(CondicaoPagamento.id == int(busca))
                else:
                    query = query.filter(False)
            else:  # nome
                query = query.filter(CondicaoPagamento.nome.ilike(f'%{busca}%'))

        condicoes = query.order_by(CondicaoPagamento.id.asc()).all()

    return render_template(
        'cadastros/condicao_pgto.html',
        condicoes=condicoes,
        busca=busca,
        status=status,
        tipo_busca=tipo_busca,
    )


from sabmec.routes.cadastros.condicao_pagamento_novo import condicao_pgto_novo
from sabmec.routes.cadastros.condicao_pagamento_editar import condicoes_pagamento_editar
from sabmec.routes.cadastros.condicao_pagamento_excluir import condicao_pgto_excluir