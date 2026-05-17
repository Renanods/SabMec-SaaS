from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    IntegerField,
    SelectField,
    BooleanField,
    TextAreaField,
    SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class FormVeiculo(FlaskForm):
    pessoa_id = SelectField(
        "Proprietario*",
        coerce=int,
        choices=[(0, "Selecione...")],
        validators=[DataRequired()],
    )

    placa = StringField(
        "Placa*",
        validators=[
            DataRequired(),
            Length(max=10),
        ],
    )

    marca = StringField(
        "Marca*",
        validators=[
            DataRequired(),
            Length(max=60),
        ],
    )

    modelo = StringField(
        "Modelo*",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )

    ano_fabricacao = IntegerField(
        "Ano fabricacao",
        validators=[
            Optional(),
            NumberRange(min=1900, max=2100, message="Informe um ano valido."),
        ],
    )

    ano_modelo = IntegerField(
        "Ano modelo",
        validators=[
            Optional(),
            NumberRange(min=1900, max=2100, message="Informe um ano valido."),
        ],
    )

    cor = StringField(
        "Cor",
        validators=[
            Optional(),
            Length(max=50),
        ],
    )

    chassi = StringField(
        "Chassi",
        validators=[
            Optional(),
            Length(max=30),
        ],
    )

    renavam = StringField(
        "Renavam",
        validators=[
            Optional(),
            Length(max=20),
        ],
    )

    observacao = TextAreaField(
        "Observacao",
        validators=[Optional()],
    )

    ativo = BooleanField("Ativo", default=True)

    submit = SubmitField("Salvar")
