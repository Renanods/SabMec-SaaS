from sabmec import db
from flask_login import UserMixin
from sabmec.models.estados_cidades import Cidade, Estado


class Pessoa(db.Model):
    __tablename__ = "pessoas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    nome_fantasia = db.Column(db.String(150))
    documento_fiscal = db.Column(db.String)
    ie_rg = db.Column(db.String)
    entidade = db.Column(db.Enum('PF', 'PJ', name='entidade_enum'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    eh_cliente = db.Column(db.Boolean)
    eh_usuario = db.Column(db.Boolean)
    eh_fornecedor = db.Column(db.Boolean)

    # Relacionamentos
    cliente = db.relationship("PessoaCliente", back_populates="pessoa", uselist=False)
    contatos = db.relationship("PessoaContato", back_populates="pessoa", cascade="all, delete-orphan")
    usuario = db.relationship("PessoaUsuario", back_populates="pessoa", uselist=False)
    fornecedor = db.relationship("PessoaFornecedor", back_populates="pessoa", uselist=False)
    enderecos = db.relationship("PessoaEndereco", back_populates="pessoa", cascade="all, delete-orphan")
    veiculos = db.relationship(
    "Veiculo",
    back_populates="pessoa",
    cascade="all, delete-orphan",
    )
    filial = db.relationship("PessoaFilial", back_populates="pessoa", uselist=False)
    
class PessoaCliente(db.Model):
    __tablename__ = "pessoas_cliente"

    pessoa_id = db.Column(db.Integer, db.ForeignKey("pessoas.id"), primary_key=True)
    cliente_ativo = db.Column(db.Boolean, default=True)

    # Relacionamentos
    pessoa = db.relationship("Pessoa", back_populates="cliente", uselist=False)

class PessoaEndereco(db.Model):
    __tablename__ = "pessoas_endereco"

    id = db.Column(db.Integer, primary_key=True)
    pessoa_id = db.Column(db.Integer, db.ForeignKey("pessoas.id"), nullable=False)
    logradouro = db.Column(db.String(150), nullable=False)
    numero = db.Column(db.String(20), default="S/N")
    complemento = db.Column(db.String(50))
    bairro = db.Column(db.String(50), nullable=False)
    cidade_id = db.Column(db.Integer, db.ForeignKey("cidades.id"), nullable=False)
    estado_id = db.Column(db.Integer, db.ForeignKey("estados.id"), nullable=False)
    cep = db.Column(db.String(10), nullable=False)
    principal = db.Column(db.Boolean, default=False)

    # Relacionamentos
    pessoa = db.relationship("Pessoa", back_populates="enderecos")
    cidade = db.relationship("Cidade")
    estado = db.relationship("Estado")

class PessoaContato(db.Model):
    __tablename__ = "pessoas_contato"

    id = db.Column(db.Integer, primary_key=True)
    pessoa_id = db.Column(db.Integer, db.ForeignKey("pessoas.id"), nullable=False)
    tipo = db.Column(db.Enum('telefone', 'whatsapp', 'email', name='tipo_contato_enum'), nullable=False)
    valor = db.Column(db.String(50), nullable=False)
    principal = db.Column(db.Boolean, default=False)

    # Relacionamentos
    pessoa = db.relationship("Pessoa", back_populates="contatos")

class PessoaUsuario(db.Model, UserMixin):
    __tablename__ = "pessoas_usuario"

    pessoa_id = db.Column(db.Integer, db.ForeignKey("pessoas.id"), primary_key=True)
    usuario = db.Column(db.String(30), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    ativo = db.Column(db.Boolean, default=True)

    # Relacionamentos
    pessoa = db.relationship("Pessoa", back_populates="usuario", uselist=False)

    def get_id(self):
        return str(self.pessoa_id)

    def __repr__(self):
        return self.usuario

class PessoaFornecedor(db.Model):
    __tablename__ = "pessoas_fornecedor"

    pessoa_id = db.Column(db.Integer, db.ForeignKey("pessoas.id"), primary_key=True)
    fornecedor_ativo = db.Column(db.Boolean, default=True)

    # Relacionamentos
    pessoa = db.relationship("Pessoa", back_populates="fornecedor", uselist=False)

class PessoaFilial(db.Model):
    __tablename__ = "pessoas_filial"

    pessoa_id = db.Column(db.Integer, db.ForeignKey("pessoas.id"), primary_key=True)
    numero_certificado = db.Column(db.Integer)
    api_google = db.Column(db.String)

    pessoa = db.relationship("Pessoa", back_populates="filial", uselist=False)
