from datetime import datetime
from decimal import Decimal

from sabmec import db


class ContaPagar(db.Model):
    __tablename__ = "contas_pagar"

    id = db.Column(db.Integer, primary_key=True)

    fornecedor_id = db.Column(
        db.Integer,
        db.ForeignKey("pessoas.id"),
        nullable=False,
        index=True,
    )

    status_id = db.Column(
        db.Integer,
        db.ForeignKey("status.id"),
        nullable=False,
        index=True,
    )

    origem = db.Column(db.String(30), nullable=False, index=True)
    referencia_id = db.Column(db.Integer, index=True)

    descricao = db.Column(db.String(255), nullable=False)
    parcela = db.Column(db.String(20))
    documento = db.Column(db.String(50))

    valor = db.Column(db.Numeric(10, 2), nullable=False)
    vencimento = db.Column(db.Date, nullable=False, index=True)

    observacao = db.Column(db.Text)

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    fornecedor = db.relationship("Pessoa")
    status = db.relationship("Status")

    baixas = db.relationship(
        "ContaPagarBaixa",
        back_populates="conta_pagar",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.Index("idx_contas_pagar_origem_ref", "origem", "referencia_id"),
        db.Index("idx_contas_pagar_status_vencimento", "status_id", "vencimento"),
        db.Index("idx_contas_pagar_fornecedor_status", "fornecedor_id", "status_id"),
    )

    @property
    def status_situacao(self):
        return self.status.situacao if self.status else None

    @property
    def valor_pago(self):
        total = Decimal("0")

        for baixa in self.baixas:
            total += baixa.valor_pago or Decimal("0")

        return total

    @property
    def valor_restante(self):
        return (self.valor or Decimal("0")) - self.valor_pago


class ContaPagarBaixa(db.Model):
    __tablename__ = "contas_pagar_baixas"

    id = db.Column(db.Integer, primary_key=True)

    conta_pagar_id = db.Column(
        db.Integer,
        db.ForeignKey("contas_pagar.id"),
        nullable=False,
        index=True,
    )

    data_pagamento = db.Column(db.Date, nullable=False, index=True)

    valor_pago = db.Column(db.Numeric(10, 2), nullable=False)
    juros = db.Column(db.Numeric(10, 2), default=0)
    multa = db.Column(db.Numeric(10, 2), default=0)
    desconto = db.Column(db.Numeric(10, 2), default=0)

    observacao = db.Column(db.Text)

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    conta_pagar = db.relationship(
        "ContaPagar",
        back_populates="baixas",
    )

    __table_args__ = (
        db.Index("idx_pagar_baixas_conta_data", "conta_pagar_id", "data_pagamento"),
    )
