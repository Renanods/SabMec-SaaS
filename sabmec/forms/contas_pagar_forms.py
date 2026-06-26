from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
    StringField,
    TextAreaField,
    DecimalField,
    IntegerField,
    DateField,
    SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class FormSemCsrf(FlaskForm):
    class Meta:
        csrf = False


class FormContaPagar(FlaskForm):
    fornecedor_id = SelectField(
        "Fornecedor*",
        coerce=int,
        choices=[(0, "Selecione...")],
        validators=[DataRequired()],
    )

    status_id = SelectField(
        "Status*",
        coerce=int,
        choices=[(0, "Selecione...")],
        validators=[DataRequired()],
    )

    origem = SelectField(
        "Origem*",
        choices=[
            ("COMPRA", "Compra"),
            ("DESPESA", "Despesa"),
            ("AVULSO", "Avulso"),
        ],
        validators=[DataRequired()],
    )

    referencia_id = IntegerField("Referencia", validators=[Optional()])

    descricao = StringField(
        "Descricao*",
        validators=[DataRequired(), Length(max=255)],
    )

    parcela = StringField(
        "Parcela",
        validators=[Optional(), Length(max=20)],
    )

    documento = StringField(
        "Documento",
        validators=[Optional(), Length(max=50)],
    )

    valor = DecimalField(
        "Valor*",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
        ],
    )

    vencimento = DateField(
        "Vencimento*",
        validators=[DataRequired()],
        format="%Y-%m-%d",
    )

    observacao = TextAreaField("Observacao", validators=[Optional()])

    submit = SubmitField("Salvar Conta")


class FormContaPagarBaixa(FormSemCsrf):
    conta_pagar_id = IntegerField(
        "Conta*",
        validators=[DataRequired()],
    )

    data_pagamento = DateField(
        "Data Pagamento*",
        validators=[DataRequired()],
        format="%Y-%m-%d",
    )

    valor_pago = DecimalField(
        "Valor Pago*",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="O valor pago deve ser maior que zero."),
        ],
    )

    juros = DecimalField(
        "Juros",
        places=2,
        default=0,
        validators=[Optional(), NumberRange(min=0)],
    )

    multa = DecimalField(
        "Multa",
        places=2,
        default=0,
        validators=[Optional(), NumberRange(min=0)],
    )

    desconto = DecimalField(
        "Desconto",
        places=2,
        default=0,
        validators=[Optional(), NumberRange(min=0)],
    )

    observacao = TextAreaField("Observacao", validators=[Optional()])

    submit = SubmitField("Registrar Pagamento")
