from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash
from flask_login import login_required

from sabmec import db
from sabmec.routes.cadastros.pessoas import pessoas_bp
from sabmec.forms.pessoas_forms import (
    FormPessoa,
    FormPessoaContato,
    FormPessoaEndereco,
    FormPessoaCliente,
    FormPessoaFornecedor,
    FormPessoaUsuario,
)
from sabmec.models.pessoas import (
    Pessoa,
    PessoaCliente,
    PessoaContato,
    PessoaEndereco,
    PessoaFornecedor,
    PessoaUsuario,
)
from sabmec.models.estados_cidades import Estado, Cidade


def somente_numeros(valor):
    if not valor:
        return None

    numeros = "".join(filter(str.isdigit, valor))
    return numeros or None


@pessoas_bp.route("/pessoas/novo", methods=["GET", "POST"])
@login_required
def pessoas_novo():
    form_pessoa = FormPessoa()
    form_contato = FormPessoaContato()
    form_endereco = FormPessoaEndereco()
    form_cliente = FormPessoaCliente()
    form_fornecedor = FormPessoaFornecedor()
    form_usuario = FormPessoaUsuario()

    form_endereco.estado_id.choices = [(0, "Selecione...")] + [
        (estado.id, f"{estado.nome} - {estado.uf}")
        for estado in Estado.query.order_by(Estado.nome).all()
    ]

    estado_id = request.form.get("estado_id", type=int)

    if estado_id:
        form_endereco.cidade_id.choices = [(0, "Selecione...")] + [
            (cidade.id, cidade.nome)
            for cidade in Cidade.query
                .filter_by(estado_id=estado_id)
                .order_by(Cidade.nome)
                .all()
        ]
    else:
        form_endereco.cidade_id.choices = [(0, "Selecione um estado primeiro")]

    if request.method == "POST":
        print("FORM RECEBIDO:", request.form)

        try:
            nome = request.form.get("nome")
            documento_fiscal = request.form.get("documento_fiscal")
            entidade = request.form.get("entidade") or "PF"

            if not nome:
                flash("Informe o nome.", "warning")
                return render_template(
                    "pessoas/pessoas_novo.html",
                    form_pessoa=form_pessoa,
                    form_contato=form_contato,
                    form_endereco=form_endereco,
                    form_cliente=form_cliente,
                    form_fornecedor=form_fornecedor,
                    form_usuario=form_usuario,
                )

            if not documento_fiscal:
                flash("Informe o CPF/CNPJ.", "warning")
                return render_template(
                    "pessoas/pessoas_novo.html",
                    form_pessoa=form_pessoa,
                    form_contato=form_contato,
                    form_endereco=form_endereco,
                    form_cliente=form_cliente,
                    form_fornecedor=form_fornecedor,
                    form_usuario=form_usuario,
                )

            pessoa = Pessoa(
                nome=nome.upper(),
                nome_fantasia=request.form.get("nome_fantasia").upper() or None,
                documento_fiscal=somente_numeros(documento_fiscal),
                ie_rg=somente_numeros(request.form.get("ie_rg")),
                entidade=entidade,
                ativo=True if request.form.get("ativo") else False,
                eh_cliente=True if request.form.get("eh_cliente") else False,
                eh_fornecedor=True if request.form.get("eh_fornecedor") else False,
                eh_usuario=True if request.form.get("eh_usuario") else False,
            )

            db.session.add(pessoa)
            db.session.flush()

            cep = request.form.get("cep")
            logradouro = request.form.get("logradouro")
            bairro = request.form.get("bairro")
            cidade_id = request.form.get("cidade_id", type=int)
            estado_id = request.form.get("estado_id", type=int)

            tem_endereco = any([
                cep,
                logradouro,
                bairro,
                cidade_id and cidade_id != 0,
                estado_id and estado_id != 0,
            ])

            if tem_endereco:
                if not cep or not logradouro or not bairro or not cidade_id or cidade_id == 0 or not estado_id or estado_id == 0:
                    flash("Se preencher endereço, informe CEP, logradouro, bairro, estado e cidade.", "warning")
                    db.session.rollback()
                    return render_template(
                        "pessoas/pessoas_novo.html",
                        form_pessoa=form_pessoa,
                        form_contato=form_contato,
                        form_endereco=form_endereco,
                        form_cliente=form_cliente,
                        form_fornecedor=form_fornecedor,
                        form_usuario=form_usuario,
                    )

                endereco = PessoaEndereco(
                    pessoa_id=pessoa.id,
                    cep=cep,
                    logradouro=logradouro.upper(),
                    numero=request.form.get("numero") or "S/N",
                    bairro=bairro.upper(),
                    complemento=request.form.get("complemento").upper() or None,
                    estado_id=estado_id,
                    cidade_id=cidade_id,
                    principal=True if request.form.get("principal") else False,
                )

                db.session.add(endereco)

            contato_valor = request.form.get("valor")

            if contato_valor:
                contato = PessoaContato(
                    pessoa_id=pessoa.id,
                    tipo=request.form.get("tipo") or "telefone",
                    valor=contato_valor,
                    principal=True if request.form.get("principal") else False,
                )

                db.session.add(contato)

            if request.form.get("eh_cliente"):
                cliente = PessoaCliente(
                    pessoa_id=pessoa.id,
                    cliente_ativo=True if request.form.get("cliente_ativo") else False,
                )
                db.session.add(cliente)

            if request.form.get("eh_fornecedor"):
                fornecedor = PessoaFornecedor(
                    pessoa_id=pessoa.id,
                    fornecedor_ativo=True if request.form.get("fornecedor_ativo") else False,
                )
                db.session.add(fornecedor)

            if request.form.get("eh_usuario"):
                usuario_nome = request.form.get("usuario")
                senha = request.form.get("senha")

                if not usuario_nome or not senha:
                    flash("Para criar usuário, informe usuário e senha.", "warning")
                    db.session.rollback()
                    return render_template(
                        "pessoas/pessoas_novo.html",
                        form_pessoa=form_pessoa,
                        form_contato=form_contato,
                        form_endereco=form_endereco,
                        form_cliente=form_cliente,
                        form_fornecedor=form_fornecedor,
                        form_usuario=form_usuario,
                    )

                usuario = PessoaUsuario(
                    pessoa_id=pessoa.id,
                    usuario=usuario_nome.upper(),
                    senha_hash=generate_password_hash(senha),
                    ativo=True if request.form.get("usuario_ativo") else True,
                )

                db.session.add(usuario)

            db.session.commit()

            return redirect(url_for("pessoas.pessoas"))

        except Exception as erro:
            db.session.rollback()
            print("ERRO AO SALVAR PESSOA:", erro)


    return render_template(
        "cadastros/pessoas_novo.html",
        form_pessoa=form_pessoa,
        form_contato=form_contato,
        form_endereco=form_endereco,
        form_cliente=form_cliente,
        form_fornecedor=form_fornecedor,
        form_usuario=form_usuario,
    )


@pessoas_bp.route("/cidades/por-estado/<int:estado_id>")
@login_required
def cidades_por_estado(estado_id):
    cidades = Cidade.query.filter_by(estado_id=estado_id).order_by(Cidade.nome).all()

    return jsonify({
        "cidades": [
            {"id": cidade.id, "nome": cidade.nome}
            for cidade in cidades
        ]
    })
