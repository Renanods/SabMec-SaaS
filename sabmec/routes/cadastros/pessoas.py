from flask import Blueprint, render_template, request
from sabmec.models.pessoas import Pessoa
from flask_login import login_required

pessoas_bp = Blueprint("pessoas", __name__)

@pessoas_bp.route("/pessoas")
@login_required
def pessoas():
    pesquisar = request.args.get("pesquisar")
    busca = request.args.get("busca", "").strip()
    tipo_pessoa = request.args.get("tipo_pessoa", "")
    tipo_busca = request.args.get("tipo_busca", "codigo")
    status = request.args.get("status", "")

    if not pesquisar:
        return render_template(
            "cadastros/pessoas.html",
            pessoas=[],
            busca=busca,
            tipo_busca=tipo_busca,
            tipo_pessoa_selecionado=tipo_pessoa,
            status=status,
        )

    query = Pessoa.query

    if busca:
        if tipo_busca == "codigo" and busca.isdigit():
            query = query.filter(Pessoa.id == int(busca))
        elif tipo_busca == "cpf":
            documento = "".join(filter(str.isdigit, busca))
            query = query.filter(Pessoa.documento_fiscal.ilike(f"%{documento}%"))
        else:
            query = query.filter(Pessoa.nome.ilike(f"%{busca.upper()}%"))

    if tipo_pessoa == "cliente":
        query = query.filter(Pessoa.eh_cliente.is_(True))
    elif tipo_pessoa == "fornecedor":
        query = query.filter(Pessoa.eh_fornecedor.is_(True))
    elif tipo_pessoa == "usuario":
        query = query.filter(Pessoa.eh_usuario.is_(True))

    if status == "ativo":
        query = query.filter(Pessoa.ativo.is_(True))
    elif status == "inativo":
        query = query.filter(Pessoa.ativo.is_(False))

    pessoas_lista = query.order_by(Pessoa.id.asc()).all()

    return render_template(
        "cadastros/pessoas.html",
        pessoas=pessoas_lista,
        busca=busca,
        tipo_busca=tipo_busca,
        tipo_pessoa_selecionado=tipo_pessoa,
        status=status,
    )

# Outras rotas em outros arquivos
from . import pessoas_novo, pessoas_editar, pessoas_excluir