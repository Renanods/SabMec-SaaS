from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


app = Flask(__name__)

caminho = "sqlite:///comunidade.db"
app.config["SQLALCHEMY_DATABASE_URI"] = caminho
app.config["SECRET_KEY"] = 'P&tS!x'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Você precisa fazer login para acessar esta página"
login_manager.login_message_category = "warning"


# Models
from sabmec.models.pessoas import Pessoa, PessoaUsuario, PessoaCliente, PessoaContato, PessoaEndereco, PessoaFilial, PessoaFornecedor
from sabmec.models.veiculos import Veiculo
from sabmec.models.cond_forma_pgto import FormaPagamento, CondicaoPagamento, CondicaoPagamentoParcela
from sabmec.models.ordem_servico import OrdemServico, OrdemServicoItem, OrdemServicoPagamento, OrdemServicoParcela
from sabmec.models.tipos import Status
from sabmec.models.contas_receber import ContaReceber, ContaReceberBaixa
from sabmec.models.contas_pagar import ContaPagar, ContaPagarBaixa
from sabmec.models.config import ConfiguracaoOs
from sabmec.models.agendamento import Agendamento
from sabmec.models.compra import Compra, CompraItem

@login_manager.user_loader
def load_usuario(id_usuario):
    return PessoaUsuario.query.get(int(id_usuario))





# Registro das rotas
from sabmec.routes.auth.login import auth_bp
from sabmec.routes.main.home import main_bp
from sabmec.routes.cadastros.pessoas import pessoas_bp
from sabmec.routes.cadastros.itens import itens_bp
from sabmec.routes.cadastros.veiculos import veiculos_bp
from sabmec.routes.comercial.os.os import os_bp
from sabmec.routes.cadastros.condicao_pagamento import condicao_pgto_bp
from sabmec.routes.financeiro.contas_receber import contas_receber_bp
from sabmec.routes.financeiro.contas_pagar import contas_pagar_bp
from sabmec.routes.impressoes.comercial.impressao_os import impressao_os_bp
from sabmec.routes.configuracao.config import configuracoes_bp
from sabmec.routes.comercial.agendamentos.agendamentos import agendamentos_bp
from sabmec.routes.comercial.compras.compras import compras_bp

app.register_blueprint(auth_bp) # Autenticação (Login, Logoff)
app.register_blueprint(main_bp) # Home e Dashboard
app.register_blueprint(pessoas_bp) # Cadastros de pessoas
app.register_blueprint(itens_bp) # Cadastros de itens
app.register_blueprint(veiculos_bp) # Cadastros de veículos
app.register_blueprint(os_bp) # Ordem de serviço
app.register_blueprint(condicao_pgto_bp) # Cadastro de condições de pgto
app.register_blueprint(contas_receber_bp) # Contas a receber
app.register_blueprint(contas_pagar_bp) # Contas a pagar
app.register_blueprint(impressao_os_bp) # Impressões da OS
app.register_blueprint(configuracoes_bp) # Configurações
app.register_blueprint(agendamentos_bp) # Configurações
app.register_blueprint(compras_bp) # Compras / Entradas

@app.context_processor
def inject_empresa_sidebar():

    filial = PessoaFilial.query.first()

    empresa = None

    if filial:
        empresa = Pessoa.query.get(
            filial.pessoa_id
        )

    return dict(
        empresa_sidebar=empresa
    )
