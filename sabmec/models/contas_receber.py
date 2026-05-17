from datetime import datetime
from decimal import Decimal

from sabmec import db


class ContaReceber(db.Model):
    __tablename__ = "contas_receber"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(
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

    valor = db.Column(db.Numeric(10, 2), nullable=False)
    vencimento = db.Column(db.Date, nullable=False, index=True)

    observacao = db.Column(db.Text)

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    cliente = db.relationship("Pessoa")
    status = db.relationship("Status")

    baixas = db.relationship(
        "ContaReceberBaixa",
        back_populates="conta_receber",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.Index("idx_contas_receber_origem_ref", "origem", "referencia_id"),
        db.Index("idx_contas_receber_status_vencimento", "status_id", "vencimento"),
        db.Index("idx_contas_receber_cliente_status", "cliente_id", "status_id"),
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


class ContaReceberBaixa(db.Model):
    __tablename__ = "contas_receber_baixas"

    id = db.Column(db.Integer, primary_key=True)

    conta_receber_id = db.Column(
        db.Integer,
        db.ForeignKey("contas_receber.id"),
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

    conta_receber = db.relationship(
        "ContaReceber",
        back_populates="baixas",
    )

    __table_args__ = (
        db.Index("idx_baixas_conta_data", "conta_receber_id", "data_pagamento"),
    )
