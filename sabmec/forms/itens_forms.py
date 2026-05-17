from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DecimalField,
    IntegerField,
    SelectField,
    BooleanField,
    SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class FormSemCsrf(FlaskForm):
    class Meta:
        csrf = False


class FormItem(FlaskForm):
    nome = StringField(
        "Nome*",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
    )

    preco = DecimalField(
        "Preco de venda*",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0, message="O preco deve ser maior ou igual a zero."),
        ],
    )

    tipo = SelectField(
        "Tipo*",
        choices=[
            ("Produto", "Produto"),
            ("Servico", "Servico"),
        ],
        validators=[DataRequired()],
    )

    ativo = BooleanField("Ativo", default=True)

    submit = SubmitField("Salvar")


class FormItemProduto(FormSemCsrf):
    estoque = IntegerField(
        "Estoque",
        default=0,
        validators=[
            Optional(),
            NumberRange(min=0, message="O estoque deve ser maior ou igual a zero."),
        ],
    )

    custo = DecimalField(
        "Custo*",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0, message="O custo deve ser maior ou igual a zero."),
        ],
    )

    submit = SubmitField("Salvar Produto")


class FormItemServico(FormSemCsrf):
    submit = SubmitField("Salvar Servico")
