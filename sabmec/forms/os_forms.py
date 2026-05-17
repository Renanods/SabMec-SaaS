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


class FormOrdemServico(FlaskForm):
    cliente_id = SelectField(
        "Cliente*",
        coerce=int,
        choices=[(0, "Selecione...")],
        validators=[DataRequired()],
    )

    veiculo_id = SelectField(
        "Veiculo*",
        coerce=int,
        choices=[(0, "Selecione um cliente primeiro")],
        validators=[DataRequired()],
    )

    data_previsao = DateField(
        "Previsao",
        validators=[Optional()],
        format="%Y-%m-%d",
    )

    km = IntegerField(
        "KM",
        validators=[
            Optional(),
            NumberRange(min=0, message="O KM não pode ser negativo."),
        ],
    )

    relato_cliente = TextAreaField(
        "Relato do cliente",
        validators=[Optional()],
    )

    diagnostico = TextAreaField(
        "Diagnostico",
        validators=[Optional()],
    )

    observacao = TextAreaField(
        "Observacao",
        validators=[Optional()],
    )

    desconto = DecimalField(
        "Desconto",
        places=2,
        default=0,
        validators=[
            Optional(),
            NumberRange(min=0, message="O desconto não pode ser negativo."),
        ],
    )

    acrescimo = DecimalField(
        "Acrescimo",
        places=2,
        default=0,
        validators=[
            Optional(),
            NumberRange(min=0, message="O acrescimo não pode ser negativo."),
        ],
    )

    submit = SubmitField("Salvar OS")


class FormOrdemServicoItem(FormSemCsrf):
    item_id = SelectField(
        "Item*",
        coerce=int,
        choices=[(0, "Selecione...")],
        validators=[DataRequired()],
    )

    tipo = SelectField(
        "Tipo*",
        choices=[
            ("Produto", "Produto"),
            ("Servico", "Servico"),
        ],
        validators=[DataRequired()],
    )

    descricao = StringField(
        "Descricao*",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
    )

    quantidade = DecimalField(
        "Quantidade*",
        places=3,
        default=1,
        validators=[
            DataRequired(),
            NumberRange(min=0.001, message="A quantidade deve ser maior que zero."),
        ],
    )

    valor_unitario = DecimalField(
        "Valor unitario*",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="O valor unitario deve ser maior que zero."),
        ],
    )

    desconto = DecimalField(
        "Desconto",
        places=2,
        default=0,
        validators=[
            Optional(),
            NumberRange(min=0, message="O desconto não pode ser negativo."),
        ],
    )

    submit = SubmitField("Adicionar Item")


class FormOrdemServicoPagamento(FormSemCsrf):
    condicao_pagamento_id = SelectField(
        "Condicao de pagamento*",
        coerce=int,
        choices=[(0, "Selecione...")],
        validators=[DataRequired()],
    )

    submit = SubmitField("Gerar Parcelas")


class FormOrdemServicoParcela(FormSemCsrf):
    numero = IntegerField(
        "Parcela*",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="O numero da parcela deve ser maior que zero."),
        ],
    )

    vencimento = DateField(
        "Vencimento*",
        validators=[DataRequired()],
        format="%Y-%m-%d",
    )

    valor = DecimalField(
        "Valor*",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="O valor da parcela deve ser maior que zero."),
        ],
    )

    submit = SubmitField("Salvar Parcela")
