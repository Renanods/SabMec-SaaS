from sabmec import db

class FormaPagamento(db.Model):
    __tablename__ = "formas_pagamento"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    codigo_tpag = db.Column(db.String(2), nullable=False)  # tPag SEFAZ
    ativo = db.Column(db.Boolean, default=True)

    condicoes = db.relationship("CondicaoPagamento", back_populates="forma_pagamento")


class CondicaoPagamento(db.Model):
    __tablename__ = "condicoes_pagamento"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    forma_pagamento_id = db.Column(db.Integer, db.ForeignKey("formas_pagamento.id"), nullable=False)
    a_vista = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)

    forma_pagamento = db.relationship("FormaPagamento", back_populates="condicoes")
    parcelas = db.relationship(
        "CondicaoPagamentoParcela",
        back_populates="condicao",
        cascade="all, delete-orphan",
        order_by="CondicaoPagamentoParcela.numero",
    )

class CondicaoPagamentoParcela(db.Model):
    __tablename__ = "condicoes_pagamento_parcela"

    id = db.Column(db.Integer, primary_key=True)
    condicao_id = db.Column(db.Integer, db.ForeignKey("condicoes_pagamento.id"), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    dias = db.Column(db.Integer, default=0)
    percentual = db.Column(db.Numeric(10, 4), nullable=False)

    condicao = db.relationship("CondicaoPagamento", back_populates="parcelas")