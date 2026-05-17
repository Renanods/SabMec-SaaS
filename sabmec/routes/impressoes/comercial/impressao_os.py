import os as os_sistema
from io import BytesIO

from flask import (
    Blueprint,
    render_template,
    make_response,
    current_app
)

from flask_login import login_required

from xhtml2pdf import pisa

from sabmec.models.ordem_servico import OrdemServico
from sabmec.models.pessoas import (
    Pessoa,
    PessoaContato,
    PessoaFilial
)

from sabmec.models.config import ConfiguracaoOs


impressao_os_bp = Blueprint(
    "impressao_os",
    __name__
)


@impressao_os_bp.route("/os/<int:id>/pdf")
@login_required
def imprimir(id):

    # Ordem de serviço
    os = OrdemServico.query.get_or_404(id)

    # Filial
    filial = PessoaFilial.query.first()

    if not filial:
        return "Nenhuma filial cadastrada."

    # Empresa
    empresa = Pessoa.query.get(filial.pessoa_id)

    if not empresa:
        return "Empresa não encontrada."

    # Contato principal
    contato = PessoaContato.query.filter_by(
        pessoa_id=filial.pessoa_id,
        principal=True
    ).first()

    # Configuração impressão
    modelo = ConfiguracaoOs.query.first()

    if not modelo:
        return "Configuração de impressão não encontrada."

    # Caminho da logo
    logo_path = None

    upload_folder = os_sistema.path.join(
        current_app.root_path,
        "static",
        "img",
        "uploads"
    )

    if os_sistema.path.exists(upload_folder):

        for arquivo in os_sistema.listdir(upload_folder):

            if arquivo.lower().startswith("logo_sistema."):

                logo_path = os_sistema.path.join(
                    upload_folder,
                    arquivo
                )

                break

    # Template impressão
    template = (
        f"comercial/impressoes/os{modelo.modelo_os}.html"
    )

    # HTML renderizado
    impressao = render_template(
        template,
        os=os,
        empresa=empresa,
        contato=contato,
        rodape=modelo.texto_rodape_os,
        logo_path=logo_path
    )

    # Buffer PDF
    pdf = BytesIO()

    # Gerar PDF
    pisa_status = pisa.CreatePDF(
        src=impressao,
        dest=pdf,
        encoding="utf-8"
    )

    # Verifica erro
    if pisa_status.err:
        return "Erro ao gerar PDF."

    pdf.seek(0)

    # Response
    response = make_response(
        pdf.getvalue()
    )

    response.headers["Content-Type"] = (
        "application/pdf"
    )

    response.headers["Content-Disposition"] = (
        f"inline; filename=os_{id}.pdf"
    )

    response.headers["Cache-Control"] = (
        "no-cache"
    )

    return response