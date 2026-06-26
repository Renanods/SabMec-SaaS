from sabmec import db
from datetime import datetime
from sqlalchemy import Index


STATUS_COMPRA_PENDENTE = "PENDENTE"
STATUS_COMPRA_CONFIRMADA = "CONFIRMADA"
STATUS_COMPRA_CANCELADA = "CANCELADA"

class Compra(db.Model):
    __tablename__ = 'compras'

    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('pessoas.id'), nullable=False, index=True)
    
    data_emissao = db.Column(db.DateTime, nullable=False)
    data_entrada = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    numero_nota = db.Column(db.Integer, nullable=False)
    serie_nota = db.Column(db.String(10), nullable=False)
    chave_acesso = db.Column(db.String(44), nullable=False, unique=True, index=True)
    
    valor_produtos = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_COMPRA_PENDENTE, index=True)
    cancelado_em = db.Column(db.DateTime)
    
    xml_original = db.Column(db.Text, nullable=True) # Guarda o XML da nota se necessário para auditoria

    # Relacionamentos
    fornecedor = db.relationship('Pessoa', foreign_keys=[fornecedor_id])
    itens = db.relationship('CompraItem', back_populates='compra', cascade='all, delete-orphan', order_by='CompraItem.id')

    def __repr__(self):
        return f"<Compra NF {self.numero_nota}-{self.serie_nota}>"


class CompraItem(db.Model):
    __tablename__ = 'compras_item'

    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=True)
    
    codigo_fornecedor = db.Column(db.String(50), nullable=True) # cProd do XML
    descricao_fornecedor = db.Column(db.String(255), nullable=True) # xProd do XML
    
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)

    # Relacionamentos
    compra = db.relationship('Compra', back_populates='itens')
    item = db.relationship('Item')

    def __repr__(self):
        return f"<CompraItem {self.descricao_fornecedor or self.item_id}>"


# Indices adicionais de pesquisa
Index('ix_compra_fornecedor_data', Compra.fornecedor_id, Compra.data_entrada)
Index('ix_compra_item_compra_id', CompraItem.compra_id)
Index('ix_compra_item_item_id', CompraItem.item_id)
