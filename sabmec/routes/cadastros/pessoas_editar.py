from flask import render_template, request, redirect, url_for, flash, jsonify
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
)
from sabmec.models.estados_cidades import Estado, Cidade
from flask_login import login_required

def somente_numeros(valor):
    if not valor:
        return None

    numeros = "".join(filter(str.isdigit, valor))
    return numeros or None


def texto_upper(valor):
    if not valor:
        return None

    valor = valor.strip()
    return valor.upper() if valor else None


def carregar_choices_endereco(form_endereco):
    form_endereco.estado_id.choices = [(0, "Selecione...")] + [
        (estado.id, f"{estado.nome} - {estado.uf}")
        for estado in Estado.query.order_by(Estado.nome).all()
    ]

    form_endereco.cidade_id.choices = [(0, "Selecione um estado primeiro")]


def renderizar_edicao(
    pessoa,
    form_pessoa,
    form_contato,
    form_endereco,
    form_cliente,
    form_fornecedor,
    form_usuario,
):
    estados = Estado.query.order_by(Estado.nome).all()

    return render_template(
        "cadastros/pessoas_editar.html",
        pessoa=pessoa,
        estados=estados,
        form_pessoa=form_pessoa,
        form_contato=form_contato,
        form_endereco=form_endereco,
        form_cliente=form_cliente,
        form_fornecedor=form_fornecedor,
        form_usuario=form_usuario,
    )


@pessoas_bp.route("/pessoas/<int:id>/editar", methods=["GET", "POST"])
@login_required
def pessoas_editar(id):
    pessoa = Pessoa.query.get_or_404(id)

    form_pessoa = FormPessoa()
    form_contato = FormPessoaContato()
    form_endereco = FormPessoaEndereco()
    form_cliente = FormPessoaCliente()
    form_fornecedor = FormPessoaFornecedor()
    form_usuario = FormPessoaUsuario()

    carregar_choices_endereco(form_endereco)

    if request.method == "GET":
        form_pessoa.nome.data = pessoa.nome
        form_pessoa.documento_fiscal.data = pessoa.documento_fiscal
        form_pessoa.nome_fantasia.data = pessoa.nome_fantasia
        form_pessoa.ie_rg.data = pessoa.ie_rg
        form_pessoa.entidade.data = pessoa.entidade
        form_pessoa.ativo.data = pessoa.ativo
        form_pessoa.eh_cliente.data = pessoa.eh_cliente
        form_pessoa.eh_fornecedor.data = pessoa.eh_fornecedor
        form_pessoa.eh_usuario.data = pessoa.eh_usuario

        if pessoa.cliente:
            form_cliente.cliente_ativo.data = pessoa.cliente.cliente_ativo

        if pessoa.fornecedor:
            form_fornecedor.fornecedor_ativo.data = pessoa.fornecedor.fornecedor_ativo

        if pessoa.usuario:
            form_usuario.usuario.data = pessoa.usuario.usuario
            form_usuario.usuario_ativo.data = pessoa.usuario.ativo


    if pessoa.filial:
        return renderizar_edicao(
            pessoa,
            form_pessoa,
            form_contato,
            form_endereco,
            form_cliente,
            form_fornecedor,
            form_usuario,
        )

    if request.method == "POST":
        acoes = request.form.getlist("acao")
        acao = acoes[-1] if acoes else "salvar_pessoa"

        try:
            if acao == "adicionar_contato":
                tipo = request.form.get("tipo") or "telefone"
                valor = request.form.get("valor")

                if not valor:
                    flash("Informe o contato.", "warning")
                    return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

                if request.form.get("contato_principal"):
                    for item in pessoa.contatos:
                        item.principal = False

                contato = PessoaContato(
                    pessoa_id=pessoa.id,
                    tipo=tipo,
                    valor=valor.strip().upper(),
                    principal=True if request.form.get("contato_principal") else False,
                )

                db.session.add(contato)
                db.session.commit()
                flash("Contato adicionado com sucesso.", "success")
                return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

            if acao.startswith("editar_contato:"):
                contato_id = int(acao.split(":")[1])
                contato = PessoaContato.query.filter_by(
                    id=contato_id,
                    pessoa_id=pessoa.id,
                ).first_or_404()

                valor = request.form.get(f"valor_contato_{contato.id}")

                if not valor:
                    flash("Informe o contato.", "warning")
                    return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

                if request.form.get(f"contato_principal_{contato.id}"):
                    for item in pessoa.contatos:
                        item.principal = False
                    contato.principal = True
                else:
                    contato.principal = False

                contato.tipo = request.form.get(f"tipo_contato_{contato.id}") or "telefone"
                contato.valor = valor.strip().upper()

                db.session.commit()
                flash("Contato atualizado com sucesso.", "success")
                return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

            if acao.startswith("excluir_contato:"):
                contato_id = int(acao.split(":")[1])
                contato = PessoaContato.query.filter_by(
                    id=contato_id,
                    pessoa_id=pessoa.id,
                ).first_or_404()

                db.session.delete(contato)
                db.session.commit()
                flash("Contato excluído com sucesso.", "success")
                return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

            if acao.startswith("definir_contato_principal:"):
                contato_id = int(acao.split(":")[1])
                contato = PessoaContato.query.filter_by(
                    id=contato_id,
                    pessoa_id=pessoa.id,
                ).first_or_404()

                for item in pessoa.contatos:
                    item.principal = False

                contato.principal = True
                db.session.commit()
                flash("Contato principal atualizado.", "success")
                return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

            if acao == "adicionar_endereco":
                cep = request.form.get("cep")
                logradouro = texto_upper(request.form.get("logradouro"))
                bairro = texto_upper(request.form.get("bairro"))
                estado_id = request.form.get("estado_id", type=int)
                cidade_id = request.form.get("cidade_id", type=int)

                if not cep or not logradouro or not bairro or not estado_id or estado_id == 0 or not cidade_id or cidade_id == 0:
                    flash("Informe CEP, logradouro, bairro, estado e cidade.", "warning")
                    return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

                if request.form.get("principal"):
                    for item in pessoa.enderecos:
                        item.principal = False

                endereco = PessoaEndereco(
                    pessoa_id=pessoa.id,
                    cep=cep,
                    logradouro=logradouro,
                    numero=texto_upper(request.form.get("numero")) or "S/N",
                    bairro=bairro,
                    complemento=texto_upper(request.form.get("complemento")),
                    estado_id=estado_id,
                    cidade_id=cidade_id,
                    principal=True if request.form.get("principal") else False,
                )

                db.session.add(endereco)
                db.session.commit()
                flash("Endereço adicionado com sucesso.", "success")
                return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

            if acao.startswith("editar_endereco:"):
                endereco_id = int(acao.split(":")[1])
                endereco = PessoaEndereco.query.filter_by(
                    id=endereco_id,
                    pessoa_id=pessoa.id,
                ).first_or_404()

                cep = request.form.get(f"cep_{endereco.id}")
                logradouro = texto_upper(request.form.get(f"logradouro_{endereco.id}"))
                bairro = texto_upper(request.form.get(f"bairro_{endereco.id}"))
                estado_id = request.form.get(f"estado_id_{endereco.id}", type=int)
                cidade_id = request.form.get(f"cidade_id_{endereco.id}", type=int)

                if not cep or not logradouro or not bairro or not estado_id or estado_id == 0 or not cidade_id or cidade_id == 0:
                    flash("Informe CEP, logradouro, bairro, estado e cidade.", "warning")
                    return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

                if request.form.get(f"principal_{endereco.id}"):
                    for item in pessoa.enderecos:
                        item.principal = False
                    endereco.principal = True
                else:
                    endereco.principal = False

                endereco.cep = cep
                endereco.logradouro = logradouro
                endereco.numero = texto_upper(request.form.get(f"numero_{endereco.id}")) or "S/N"
                endereco.bairro = bairro
                endereco.complemento = texto_upper(request.form.get(f"complemento_{endereco.id}"))
                endereco.estado_id = estado_id
                endereco.cidade_id = cidade_id

                db.session.commit()
                flash("Endereço atualizado com sucesso.", "success")
                return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

            if acao.startswith("excluir_endereco:"):
                endereco_id = int(acao.split(":")[1])
                endereco = PessoaEndereco.query.filter_by(
                    id=endereco_id,
                    pessoa_id=pessoa.id,
                ).first_or_404()

                db.session.delete(endereco)
                db.session.commit()
                flash("Endereço excluído com sucesso.", "success")
                return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

            if acao.startswith("definir_endereco_principal:"):
                endereco_id = int(acao.split(":")[1])
                endereco = PessoaEndereco.query.filter_by(
                    id=endereco_id,
                    pessoa_id=pessoa.id,
                ).first_or_404()

                for item in pessoa.enderecos:
                    item.principal = False

                endereco.principal = True
                db.session.commit()
                flash("Endereço principal atualizado.", "success")
                return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

            nome = texto_upper(request.form.get("nome"))
            documento_fiscal = somente_numeros(request.form.get("documento_fiscal"))

            if not nome:
                flash("Informe o nome.", "warning")
                return renderizar_edicao(
                    pessoa,
                    form_pessoa,
                    form_contato,
                    form_endereco,
                    form_cliente,
                    form_fornecedor,
                    form_usuario,
                )

            if not documento_fiscal:
                flash("Informe o CPF/CNPJ.", "warning")
                return renderizar_edicao(
                    pessoa,
                    form_pessoa,
                    form_contato,
                    form_endereco,
                    form_cliente,
                    form_fornecedor,
                    form_usuario,
                )

            pessoa.nome = nome
            pessoa.documento_fiscal = documento_fiscal
            pessoa.nome_fantasia = texto_upper(request.form.get("nome_fantasia"))
            pessoa.ie_rg = somente_numeros(request.form.get("ie_rg"))
            pessoa.entidade = request.form.get("entidade") or "PF"
            pessoa.ativo = True if request.form.get("ativo") else False
            pessoa.eh_cliente = True if request.form.get("eh_cliente") else False
            pessoa.eh_fornecedor = True if request.form.get("eh_fornecedor") else False
            pessoa.eh_usuario = True if request.form.get("eh_usuario") else False

            if pessoa.eh_cliente:
                if not pessoa.cliente:
                    cliente = PessoaCliente(pessoa_id=pessoa.id)
                    db.session.add(cliente)
                    pessoa.cliente = cliente

                pessoa.cliente.cliente_ativo = True if request.form.get("cliente_ativo") else False

            elif pessoa.cliente:
                db.session.delete(pessoa.cliente)

            if pessoa.eh_fornecedor:
                if not pessoa.fornecedor:
                    fornecedor = PessoaFornecedor(pessoa_id=pessoa.id)
                    db.session.add(fornecedor)
                    pessoa.fornecedor = fornecedor

                pessoa.fornecedor.fornecedor_ativo = True if request.form.get("fornecedor_ativo") else False

            elif pessoa.fornecedor:
                db.session.delete(pessoa.fornecedor)

            if pessoa.eh_usuario and pessoa.usuario:
                pessoa.usuario.usuario = texto_upper(request.form.get("usuario"))
                pessoa.usuario.ativo = True if request.form.get("usuario_ativo") else False

            db.session.commit()
            flash("Pessoa atualizada com sucesso.", "success")
            return redirect(url_for("pessoas.pessoas_editar", id=pessoa.id))

        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao atualizar pessoa: {erro}", "danger")

    return renderizar_edicao(
        pessoa,
        form_pessoa,
        form_contato,
        form_endereco,
        form_cliente,
        form_fornecedor,
        form_usuario,
    )
