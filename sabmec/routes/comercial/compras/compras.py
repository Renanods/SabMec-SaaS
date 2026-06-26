from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_

from sabmec.models.compra import Compra
from sabmec.models.pessoas import Pessoa
from sabmec.routes.comercial.compras.compras_utils import garantir_schema_compras


compras_bp = Blueprint("compras", __name__)


@compras_bp.route("/compras")
@login_required
def compras():
    garantir_schema_compras()

    pesquisar = request.args.get("pesquisar")
    busca = request.args.get("busca", "").strip()
    tipo_busca = request.args.get("tipo_busca", "nota")
    status = request.args.get("status", "")
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")

    compras_list = []

    if pesquisar:
        query = Compra.query.join(Pessoa, Compra.fornecedor_id == Pessoa.id)

        if busca:
            busca_upper = busca.upper()
            busca_numeros = "".join(filter(str.isdigit, busca))

            if tipo_busca == "nota":
                if busca_numeros:
                    query = query.filter(Compra.numero_nota == int(busca_numeros))
                else:
                    query = query.filter(False)

            elif tipo_busca == "fornecedor":
                query = query.filter(Pessoa.nome.ilike(f"%{busca_upper}%"))

            elif tipo_busca == "chave":
                query = query.filter(Compra.chave_acesso.ilike(f"%{busca_numeros or busca_upper}%"))

            else:
                filtros = [
                    Pessoa.nome.ilike(f"%{busca_upper}%"),
                    Compra.chave_acesso.ilike(f"%{busca_numeros or busca_upper}%"),
                ]
                if busca_numeros:
                    filtros.append(Compra.numero_nota == int(busca_numeros))
                query = query.filter(or_(*filtros))

        if status:
            query = query.filter(Compra.status == status)

        if data_inicio:
            query = query.filter(Compra.data_emissao >= datetime.fromisoformat(data_inicio))

        if data_fim:
            query = query.filter(Compra.data_emissao <= datetime.fromisoformat(data_fim + "T23:59:59"))

        compras_list = query.order_by(Compra.data_entrada.desc()).all()

    return render_template(
        "comercial/compras/compras.html",
        compras=compras_list,
        busca=busca,
        tipo_busca=tipo_busca,
        status=status,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


from sabmec.routes.comercial.compras import compras_cancelar, compras_conferir, compras_importar
