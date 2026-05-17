from flask import Blueprint, render_template, request
from sabmec.models.item import Item
from flask_login import login_required

itens_bp = Blueprint("itens", __name__)


@itens_bp.route("/itens")
@login_required
def itens():
    pesquisar = request.args.get("pesquisar")
    busca = request.args.get("busca", "").strip()
    tipo_busca = request.args.get("tipo_busca", "codigo")
    tipo_item = request.args.get("tipo_item", "")
    status = request.args.get("status", "")

    if not pesquisar:
        return render_template(
            "cadastros/itens.html",
            itens=[],
            busca=busca,
            tipo_busca=tipo_busca,
            tipo_item_selecionado=tipo_item,
            status=status,
        )

    query = Item.query

    if busca:
        if tipo_busca == "codigo" and busca.isdigit():
            query = query.filter(Item.id == int(busca))
        elif tipo_busca == "nome":
            query = query.filter(Item.nome.ilike(f"%{busca.upper()}%"))
        else:
            query = query.filter(Item.nome.ilike(f"%{busca.upper()}%"))

    if tipo_item:
        query = query.filter(Item.tipo == tipo_item)

    if status == "ativo":
        query = query.filter(Item.ativo.is_(True))
    elif status == "inativo":
        query = query.filter(Item.ativo.is_(False))

    itens_lista = query.order_by(Item.id.asc()).all()

    return render_template(
        "cadastros/itens.html",
        itens=itens_lista,
        busca=busca,
        tipo_busca=tipo_busca,
        tipo_item_selecionado=tipo_item,
        status=status,
    )


from . import itens_novo, itens_editar, itens_excluir