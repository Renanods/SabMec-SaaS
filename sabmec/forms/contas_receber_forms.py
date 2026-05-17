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


class FormContaReceber(FlaskForm):
    cliente_id = SelectField(
        "Cliente*",
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
            ("OS", "Ordem de Serviço"),
            ("VENDA", "Venda"),
            ("AVULSO", "Avulso"),
        ],
        validators=[DataRequired()],
    )

    referencia_id = IntegerField("Referência", validators=[Optional()])

    descricao = StringField(
        "Descrição*",
        validators=[DataRequired(), Length(max=255)],
    )

    parcela = StringField(
        "Parcela",
        validators=[Optional(), Length(max=20)],
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

    observacao = TextAreaField("Observação", validators=[Optional()])

    submit = SubmitField("Salvar Conta")


class FormContaReceberBaixa(FormSemCsrf):
    conta_receber_id = IntegerField(
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

    observacao = TextAreaField("Observação", validators=[Optional()])

    submit = SubmitField("Registrar Pagamento")
