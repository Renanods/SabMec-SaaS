import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required

from sabmec import db
from sabmec.forms.config_forms import (
    FormConfiguracaoFilial,
    FormConfiguracaoComercialOS,
)
from sabmec.models.pessoas import (
    Pessoa,
    PessoaFilial,
    PessoaEndereco,
    PessoaContato,
)
from sabmec.models.estados_cidades import Estado, Cidade
from sabmec.models.config import ConfiguracaoOs


configuracoes_bp = Blueprint("configuracoes", __name__)


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


def filial_atual():
    return PessoaFilial.query.first()


def endereco_principal(pessoa_id):
    if not pessoa_id:  # Apenas para consistência interna
        return None

    endereco = PessoaEndereco.query.filter_by(
        pessoa_id=pessoa_id,
        principal=True,
    ).first()

    if endereco:
        return endereco

    return PessoaEndereco.query.filter_by(pessoa_id=pessoa_id).first()


def contato_principal(pessoa_id):
    if not pessoa_id:
        return None

    contato = PessoaContato.query.filter_by(
        pessoa_id=pessoa_id,
        principal=True,
    ).first()

    if contato:
        return contato

    return PessoaContato.query.filter_by(pessoa_id=pessoa_id).first()


def configuracao_os_atual():
    config = ConfiguracaoOs.query.first()

    if not config:
        config = ConfiguracaoOs(
            modelo_os=1,
            texto_rodape_os=None,
        )

        db.session.add(config)
        db.session.commit()

    return config


def estados_choices():
    return Estado.query.order_by(Estado.nome.asc()).all()


def cidades_por_estado(estado_id):
    if not estado_id:
        return []

    return (
        Cidade.query
        .filter_by(estado_id=estado_id)
        .order_by(Cidade.nome.asc())
        .all()
    )


def endereco_foi_preenchido():
    estado_id = request.form.get("estado_id", type=int)
    cidade_id = request.form.get("cidade_id", type=int)

    return any([
        request.form.get("cep"),
        request.form.get("logradouro"),
        request.form.get("numero"),
        request.form.get("bairro"),
        request.form.get("complemento"),
        estado_id and estado_id != 0,
        cidade_id and cidade_id != 0,
    ])


def contato_foi_preenchido():
    return any([
        request.form.get("contato_tipo"),
        request.form.get("contato_valor"),
    ])


def renderizar_configuracoes(
    form_filial,
    form_comercial_os,
    filial,
    config_os,
    aba_ativa,
    endereco=None,
    contato=None,
    estados=None,
    cidades=None,
):
    # Lógica para verificar se a logo existe fisicamente na pasta e mandar para o HTML
    logo_atual = None
    upload_folder = os.path.join(current_app.root_path, 'static', 'img', 'uploads')
    
    # Procura se existe algum arquivo que comece com 'logo_sistema' na pasta
    if os.path.exists(upload_folder):
        arquivos = os.listdir(upload_folder)
        for arquivo in arquivos:
            if arquivo.startswith('logo_sistema.'):
                logo_atual = f"img/uploads/{arquivo}"
                break

    return render_template(
        "configuracao/config.html",
        form_filial=form_filial,
        form_comercial_os=form_comercial_os,
        filial=filial,
        config_os=config_os,
        aba_ativa=aba_ativa,
        endereco=endereco,
        contato=contato,
        estados=estados or [],
        cidades=cidades or [],
        logo_atual=logo_atual, # Passa o caminho relativo descoberto para o template
    )


@configuracoes_bp.route("/configuracoes", methods=["GET", "POST"])
@login_required
def configuracoes():
    aba_ativa = request.form.get("aba_ativa", "filial")

    form_filial = FormConfiguracaoFilial()
    form_comercial_os = FormConfiguracaoComercialOS()

    filial = filial_atual()
    config_os = configuracao_os_atual()

    pessoa_id = filial.pessoa_id if filial else None
    endereco = endereco_principal(pessoa_id)
    contato = contato_principal(pessoa_id)

    estado_id = request.form.get("estado_id", type=int)

    if not estado_id and endereco:
        estado_id = endereco.estado_id

    estados = estados_choices()
    cidades = cidades_por_estado(estado_id)

    if request.method == "GET":
        if filial and filial.pessoa:
            form_filial.nome.data = filial.pessoa.nome
            form_filial.nome_fantasia.data = filial.pessoa.nome_fantasia
            form_filial.documento_fiscal.data = filial.pessoa.documento_fiscal
            form_filial.ie_rg.data = filial.pessoa.ie_rg
            form_filial.numero_certificado.data = filial.numero_certificado
            form_filial.api_google.data = filial.api_google

        form_comercial_os.modelo_impressao_os.data = config_os.modelo_os
        form_comercial_os.texto_rodape_os.data = config_os.texto_rodape_os

        return renderizar_configuracoes(
            form_filial,
            form_comercial_os,
            filial,
            config_os,
            aba_ativa,
            endereco,
            contato,
            estados,
            cidades,
        )

    acao = request.form.get("acao")

    try:
        if acao == "salvar_filial":
            aba_ativa = "filial"

            nome = texto_upper(request.form.get("nome"))
            documento_fiscal = somente_numeros(request.form.get("documento_fiscal"))

            if not nome:
                flash("Informe a razão social da filial.", "warning")
                return renderizar_configuracoes(form_filial, form_comercial_os, filial, config_os, aba_ativa, endereco, contato, estados, cidades)

            if not documento_fiscal:
                flash("Informe o CNPJ da filial.", "warning")
                return renderizar_configuracoes(form_filial, form_comercial_os, filial, config_os, aba_ativa, endereco, contato, estados, cidades)

            if not filial:
                pessoa = Pessoa(
                    nome=nome,
                    nome_fantasia=texto_upper(request.form.get("nome_fantasia")),
                    documento_fiscal=documento_fiscal,
                    ie_rg=somente_numeros(request.form.get("ie_rg")),
                    entidade="PJ",
                    ativo=True,
                    eh_cliente=False,
                    eh_fornecedor=False,
                    eh_usuario=False,
                )

                db.session.add(pessoa)
                db.session.flush()

                filial = PessoaFilial(
                    pessoa_id=pessoa.id,
                    numero_certificado=texto_upper(request.form.get("numero_certificado")),
                    api_google=request.form.get("api_google"),
                )

                db.session.add(filial)

            else:
                filial.pessoa.nome = nome
                filial.pessoa.nome_fantasia = texto_upper(request.form.get("nome_fantasia"))
                filial.pessoa.documento_fiscal = documento_fiscal
                filial.pessoa.ie_rg = somente_numeros(request.form.get("ie_rg"))
                filial.numero_certificado = texto_upper(request.form.get("numero_certificado"))
                filial.api_google = request.form.get("api_google")

            db.session.flush()

            pessoa_id = filial.pessoa_id

            if contato_foi_preenchido():
                contato_valor = request.form.get("contato_valor")

                if not contato_valor:
                    flash("Se preencher contato, informe o valor do contato.", "warning")
                    return renderizar_configuracoes(form_filial, form_comercial_os, filial, config_os, aba_ativa, endereco, contato, estados, cidades)

                if not contato:
                    contato = PessoaContato(
                        pessoa_id=pessoa_id,
                        principal=True,
                    )
                    db.session.add(contato)

                contato.tipo = request.form.get("contato_tipo") or "telefone"
                contato.valor = contato_valor.strip()
                contato.principal = True

            if endereco_foi_preenchido():
                cep = request.form.get("cep")
                logradouro = texto_upper(request.form.get("logradouro"))
                numero = texto_upper(request.form.get("numero")) or "S/N"
                bairro = texto_upper(request.form.get("bairro"))
                complemento = texto_upper(request.form.get("complemento"))
                estado_id = request.form.get("estado_id", type=int)
                cidade_id = request.form.get("cidade_id", type=int)

                if not cep or not logradouro or not bairro or not estado_id or estado_id == 0 or not cidade_id or cidade_id == 0:
                    flash("Se preencher endereço, informe CEP, logradouro, bairro, estado e cidade.", "warning")
                    return renderizar_configuracoes(form_filial, form_comercial_os, filial, config_os, aba_ativa, endereco, contato, estados, cidades)

                if not endereco:
                    endereco = PessoaEndereco(
                        pessoa_id=pessoa_id,
                        principal=True,
                    )
                    db.session.add(endereco)

                endereco.cep = cep
                endereco.logradouro = logradouro
                endereco.numero = numero
                endereco.bairro = bairro
                endereco.complemento = complemento
                endereco.estado_id = estado_id
                endereco.cidade_id = cidade_id
                endereco.principal = True

            # --- PROCESSAMENTO DO UPLOAD DA LOGO ---
            file = request.files.get("logo_sistema")
            if file and file.filename != "":
                # Define a pasta static/img/uploads/
                upload_folder = os.path.join(current_app.root_path, "static", "img", "uploads")
                os.makedirs(upload_folder, exist_ok=True)

                # Limpa logos antigas com extensões diferentes para não acumular lixo
                if os.path.exists(upload_folder):
                    for arquivo_antigo in os.listdir(upload_folder):
                        if arquivo_antigo.startswith("logo_sistema."):
                            try:
                                os.remove(os.path.join(upload_folder, arquivo_antigo))
                            except Exception:
                                pass

                # Obtém a extensão correta e salva o novo arquivo
                extensao = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "png"
                nome_final = f"logo_sistema.{extensao}"
                
                caminho_salvar = os.path.join(upload_folder, nome_final)
                file.save(caminho_salvar)
            # --------------------------------------

            db.session.commit()

            flash("Filial salva com sucesso.", "success")
            return redirect(url_for("configuracoes.configuracoes"))

        if acao == "salvar_comercial_os":
            aba_ativa = "comercial"

            config_os.modelo_os = request.form.get("modelo_impressao_os", type=int) or 1
            config_os.texto_rodape_os = texto_upper(request.form.get("texto_rodape_os"))

            db.session.commit()

            flash("Configurações da OS salvas com sucesso.", "success")
            return redirect(url_for("configuracoes.configuracoes"))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao salvar configurações: {erro}", "danger")

    return renderizar_configuracoes(
        form_filial,
        form_comercial_os,
        filial,
        config_os,
        aba_ativa,
        endereco,
        contato,
        estados,
        cidades,
    )