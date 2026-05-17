from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional


class FormConfiguracaoFilial(FlaskForm):
    nome = StringField("Razão Social*", validators=[DataRequired()])
    nome_fantasia = StringField("Nome Fantasia")
    documento_fiscal = StringField("CNPJ*", validators=[DataRequired()])
    ie_rg = StringField("Inscrição Estadual")

    numero_certificado = StringField("Número Certificado", validators=[Optional()])
    api_google = StringField("API Google", validators=[Optional()])


class FormConfiguracaoComercialOS(FlaskForm):
    modelo_impressao_os = SelectField(
        "Modelo de Impressão da OS",
        coerce=int,
        choices=[
            (1, "Impressão 1 via com logo"),
            (2, "Impressão 2 vias com logo"),
        ],
    )

    texto_rodape_os = TextAreaField("Texto do Rodapé da OS", validators=[Optional()])
