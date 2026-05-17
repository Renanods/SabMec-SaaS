from flask import Blueprint, render_template, request
from sabmec.models.veiculos import Veiculo
from sabmec.models.pessoas import Pessoa
from flask_login import login_required

veiculos_bp = Blueprint("veiculos", __name__)

@veiculos_bp.route("/veiculos")
@login_required
def veiculos():
    pesquisar = request.args.get("pesquisar")
    busca = request.args.get("busca", "").strip()
    tipo_busca = request.args.get("tipo_busca", "codigo")
    status = request.args.get("status", "")

    if not pesquisar:
        return render_template(
            "cadastros/veiculos.html",
            veiculos=[],
            busca=busca,
            tipo_busca=tipo_busca,
            status=status,
        )

    query = Veiculo.query.join(Pessoa)

    if busca:
        busca_upper = busca.upper().strip()

        if tipo_busca == "codigo" and busca.isdigit():
            query = query.filter(Veiculo.id == int(busca))
        elif tipo_busca == "placa":
            placa = busca_upper.replace("-", "").replace(" ", "")
            query = query.filter(Veiculo.placa.ilike(f"%{placa}%"))
        elif tipo_busca == "modelo":
            query = query.filter(Veiculo.modelo.ilike(f"%{busca_upper}%"))
        elif tipo_busca == "proprietario":
            query = query.filter(Pessoa.nome.ilike(f"%{busca_upper}%"))
        else:
            query = query.filter(
                Veiculo.placa.ilike(f"%{busca_upper}%")
                | Veiculo.modelo.ilike(f"%{busca_upper}%")
                | Pessoa.nome.ilike(f"%{busca_upper}%")
            )

    if status == "ativo":
        query = query.filter(Veiculo.ativo.is_(True))
    elif status == "inativo":
        query = query.filter(Veiculo.ativo.is_(False))

    veiculos_lista = query.order_by(Veiculo.id.asc()).all()

    return render_template(
        "cadastros/veiculos.html",
        veiculos=veiculos_lista,
        busca=busca,
        tipo_busca=tipo_busca,
        status=status,
    )


from . import veiculos_novo, veiculos_editar, veiculos_excluir