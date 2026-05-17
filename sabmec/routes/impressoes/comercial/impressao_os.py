import os as os_sistema  # Importamos com um apelido para não dar conflito com a variável 'os'
from io import BytesIO

from flask import Blueprint, render_template, make_response, current_app # Usando current_app para evitar import circular
from flask_login import login_required

from xhtml2pdf import pisa

from sabmec.models.ordem_servico import OrdemServico
from sabmec.models.pessoas import Pessoa, PessoaContato
from sabmec.models.pessoas import PessoaFilial
from sabmec.models.config import ConfiguracaoOs


impressao_os_bp = Blueprint(
    "impressao_os",
    __name__
)


@impressao_os_bp.route("/os/<int:id>/pdf")
@login_required
def imprimir(id):

    # Mantemos o nome da variável como 'os' para não quebrar seus HTMLs existentes
    os = OrdemServico.query.get_or_404(id)

    filial = PessoaFilial.query.first()

    empresa = Pessoa.query.get(
        filial.pessoa_id
    )

    contato = PessoaContato.query.get(
        filial.pessoa_id
    )

    modelo = ConfiguracaoOs.query.first()

    # --- DESCOBRIR O CAMINHO ABSOLUTO DA LOGO ---
    logo_path = None
    # Usamos o 'current_app' (que substitui o 'app') e o 'os_sistema' (nosso apelido para o módulo)
    upload_folder = os_sistema.path.join(current_app.root_path, "static", "img", "uploads")
    
    if os_sistema.path.exists(upload_folder):
        for arquivo in os_sistema.listdir(upload_folder):
            if arquivo.startswith("logo_sistema."):
                # xhtml2pdf precisa do caminho real no sistema de arquivos
                logo_path = os_sistema.path.join(upload_folder, arquivo)
                break
    # --------------------------------------------

    # Pra n usar 500 if o caminho tem que conter o codigo da impressão
    template = f"comercial/impressoes/os{modelo.modelo_os}.html"

    impressao = render_template(
        template,
        os=os,  # Seus HTMLs continuam recebendo a variável 'os' normalmente
        empresa=empresa,
        contato=contato,
        rodape=modelo.texto_rodape_os,
        logo_path=logo_path
    )

    pdf = BytesIO()

    pisa.CreatePDF(
        src=impressao,
        dest=pdf
    )

    response = make_response(
        pdf.getvalue()
    )

    response.headers["Content-Type"] = "application/pdf"

    response.headers["Content-Disposition"] = (
        f"inline; filename=os_{id}.pdf"
    )

    return response