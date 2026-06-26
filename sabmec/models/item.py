from sabmec import db


class Item(db.Model):
    __tablename__ = "itens"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    tipo = db.Column(db.Enum("Produto", "Servico", name="tipo_item_enum"), nullable=False)
    ativo = db.Column(db.Boolean, default=True)

    mercadoria = db.relationship(
        "ItemMercadoria",
        back_populates="item",
        uselist=False,
        cascade="all, delete-orphan",
    )

    servico = db.relationship(
        "ItemServico",
        back_populates="item",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ItemMercadoria(db.Model):
    __tablename__ = "itens_mercadoria"

    item_id = db.Column(db.Integer, db.ForeignKey("itens.id"), primary_key=True)
    estoque = db.Column(db.Integer, default=0)
    custo = db.Column(db.Numeric(10, 2), nullable=False)
    ncm = db.Column(db.String(8), nullable=True)
    origem = db.Column(db.String(1), nullable=True)

    item = db.relationship("Item", back_populates="mercadoria")


class ItemServico(db.Model):
    __tablename__ = "itens_servico"

    item_id = db.Column(db.Integer, db.ForeignKey("itens.id"), primary_key=True)

    item = db.relationship("Item", back_populates="servico")
