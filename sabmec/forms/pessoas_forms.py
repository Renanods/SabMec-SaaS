from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, EqualTo

class FormSemCsrf(FlaskForm):
    class Meta:
        csrf = False


class FormLogin(FlaskForm):
    usuario = StringField("Usuario", validators=[DataRequired(), Length(max=30)])
    senha = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")


class FormPessoa(FlaskForm):
    nome = StringField("Nome*", validators=[DataRequired(), Length(max=150)])
    nome_fantasia = StringField("Nome Fantasia", validators=[Optional(), Length(max=150)])
    documento_fiscal = StringField("CPF / CNPJ*", validators=[DataRequired(), Length(max=20)])
    ie_rg = StringField("RG / IE", validators=[Optional(), Length(max=20)])

    entidade = SelectField(
        "Natureza*",
        choices=[("PF", "Pessoa Fisica"), ("PJ", "Pessoa Juridica")],
        validators=[DataRequired()],
    )

    ativo = BooleanField("Ativo", default=True)
    eh_cliente = BooleanField("Cliente", default=False)
    eh_fornecedor = BooleanField("Fornecedor", default=False)
    eh_usuario = BooleanField("Usuario", default=False)
    submit = SubmitField("Salvar Cadastro")


class FormPessoaContato(FormSemCsrf):
    tipo = SelectField(
        "Tipo",
        choices=[
            ("telefone", "Telefone"),
            ("whatsapp", "WhatsApp"),
            ("email", "E-mail"),
        ],
        validators=[Optional()],
    )

    valor = StringField("Contato", validators=[Optional(), Length(max=50)])
    principal = BooleanField("Contato principal", default=False)
    submit = SubmitField("Salvar")


class FormPessoaEndereco(FormSemCsrf):
    cep = StringField("CEP", validators=[Optional(), Length(max=10)])
    logradouro = StringField("Logradouro", validators=[Optional(), Length(max=150)])
    numero = StringField("Numero", default="S/N", validators=[Optional(), Length(max=20)])
    bairro = StringField("Bairro", validators=[Optional(), Length(max=50)])
    complemento = StringField("Complemento", validators=[Optional(), Length(max=50)])

    estado_id = SelectField(
        "Estado",
        coerce=int,
        choices=[(0, "Selecione...")],
        validators=[Optional()],
    )

    cidade_id = SelectField(
        "Cidade",
        coerce=int,
        choices=[(0, "Selecione um estado primeiro")],
        validators=[Optional()],
    )

    principal = BooleanField("Endereco principal", default=False)
    submit = SubmitField("Salvar")


class FormPessoaCliente(FormSemCsrf):
    cliente_ativo = BooleanField("Cliente ativo", default=True)
    submit = SubmitField("Salvar")


class FormPessoaFornecedor(FormSemCsrf):
    fornecedor_ativo = BooleanField("Fornecedor ativo", default=True)
    submit = SubmitField("Salvar")


class FormPessoaUsuario(FormSemCsrf):
    usuario = StringField("Usuario*", validators=[DataRequired(), Length(min=3, max=30)])
    senha = PasswordField("Senha*", validators=[DataRequired(), Length(min=6, max=128)])

    confirmar_senha = PasswordField(
        "Confirmar senha",
        validators=[
            Optional(),
            EqualTo("senha", message="As senhas precisam ser iguais."),
        ],
    )

    usuario_ativo = BooleanField("Usuario ativo", default=True)
    submit = SubmitField("Salvar")


class FormPessoaFilial(FormSemCsrf):
    numero_certificado = IntegerField("Numero do certificado", validators=[Optional()])
    api_google = StringField("API Google", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Salvar")
