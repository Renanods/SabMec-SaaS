from sabmec import db
from datetime import datetime
from sqlalchemy import CheckConstraint, Index


class OrdemServico(db.Model):
    __tablename__ = "ordens_servico"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("pessoas.id"), nullable=False)
    veiculo_id = db.Column(db.Integer, db.ForeignKey("veiculos.id"), nullable=False)

    data_abertura = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_previsao = db.Column(db.Date)
    data_fechamento = db.Column(db.DateTime)

    status_id = db.Column(db.Integer, db.ForeignKey("status.id"), default=1, nullable=False)

    km = db.Column(db.Integer)
    relato_cliente = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    observacao = db.Column(db.Text)

    subtotal_produtos = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    subtotal_servicos = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    desconto = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    acrescimo = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    total = db.Column(db.Numeric(10, 2), default=0, nullable=False)

    __table_args__ = (
        CheckConstraint("subtotal_produtos >= 0", name="ck_os_subtotal_produtos_nao_negativo"),
        CheckConstraint("subtotal_servicos >= 0", name="ck_os_subtotal_servicos_nao_negativo"),
        CheckConstraint("desconto >= 0", name="ck_os_desconto_nao_negativo"),
        CheckConstraint("acrescimo >= 0", name="ck_os_acrescimo_nao_negativo"),
        CheckConstraint("total >= 0", name="ck_os_total_maior_ou_igual_a_zero"),

        Index("ix_os_cliente_id", "cliente_id"),
        Index("ix_os_veiculo_id", "veiculo_id"),
        Index("ix_os_status_id", "status_id"),
        Index("ix_os_data_abertura", "data_abertura"),
        Index("ix_os_cliente_status", "cliente_id", "status_id"),
        Index("ix_os_veiculo_status", "veiculo_id", "status_id"),
        Index("ix_os_status_data_abertura", "status_id", "data_abertura"),
    )

    cliente = db.relationship("Pessoa")
    veiculo = db.relationship("Veiculo")

    itens = db.relationship(
        "OrdemServicoItem",
        back_populates="ordem_servico",
        cascade="all, delete-orphan",
    )

    pagamento = db.relationship(
        "OrdemServicoPagamento",
        back_populates="ordem_servico",
        uselist=False,
        cascade="all, delete-orphan",
    )

    status = db.relationship("Status")


class OrdemServicoItem(db.Model):
    __tablename__ = "ordens_servico_item"

    id = db.Column(db.Integer, primary_key=True)

    ordem_servico_id = db.Column(db.Integer, db.ForeignKey("ordens_servico.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("itens.id"), nullable=False)

    tipo = db.Column(db.Enum("Produto", "Servico", name="tipo_os_item_enum"), nullable=False)

    descricao = db.Column(db.String(150), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), default=1, nullable=False)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    desconto = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_os_item_quantidade_maior_que_zero"),
        CheckConstraint("valor_unitario > 0", name="ck_os_item_valor_unitario_maior_que_zero"),
        CheckConstraint("desconto >= 0", name="ck_os_item_desconto_nao_negativo"),
        CheckConstraint("total > 0", name="ck_os_item_total_maior_que_zero"),

        Index("ix_os_item_ordem_servico_id", "ordem_servico_id"),
        Index("ix_os_item_item_id", "item_id"),
        Index("ix_os_item_tipo", "tipo"),
    )

    ordem_servico = db.relationship("OrdemServico", back_populates="itens")
    item = db.relationship("Item")


class OrdemServicoPagamento(db.Model):
    __tablename__ = "ordens_servico_pagamento"

    ordem_servico_id = db.Column(
        db.Integer,
        db.ForeignKey("ordens_servico.id"),
        primary_key=True,
    )

    condicao_pagamento_id = db.Column(db.Integer, db.ForeignKey("condicoes_pagamento.id"))
    nome_condicao = db.Column(db.String(80), nullable=False)

    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade_parcelas = db.Column(db.Integer, default=1, nullable=False)

    __table_args__ = (
        CheckConstraint("valor_total > 0", name="ck_os_pagamento_valor_total_maior_que_zero"),
        CheckConstraint("quantidade_parcelas > 0", name="ck_os_pagamento_qtd_parcelas_maior_que_zero"),

        Index("ix_os_pagamento_condicao_id", "condicao_pagamento_id"),
    )

    ordem_servico = db.relationship("OrdemServico", back_populates="pagamento")
    condicao_pagamento = db.relationship("CondicaoPagamento")

    parcelas = db.relationship(
        "OrdemServicoParcela",
        back_populates="pagamento",
        cascade="all, delete-orphan",
    )


class OrdemServicoParcela(db.Model):
    __tablename__ = "ordens_servico_parcela"

    id = db.Column(db.Integer, primary_key=True)

    ordem_servico_id = db.Column(
        db.Integer,
        db.ForeignKey("ordens_servico_pagamento.ordem_servico_id"),
        nullable=False,
    )

    numero = db.Column(db.Integer, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("numero > 0", name="ck_os_parcela_numero_maior_que_zero"),
        CheckConstraint("valor > 0", name="ck_os_parcela_valor_maior_que_zero"),

        Index("ix_os_parcela_ordem_servico_id", "ordem_servico_id"),
        Index("ix_os_parcela_vencimento", "vencimento"),
        Index("ix_os_parcela_os_vencimento", "ordem_servico_id", "vencimento"),
    )

    pagamento = db.relationship("OrdemServicoPagamento", back_populates="parcelas")
