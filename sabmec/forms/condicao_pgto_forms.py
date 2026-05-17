
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from sabmec.models.cond_forma_pgto import FormaPagamento


class CondicaoPagamentoForm(FlaskForm):
    nome = StringField(
        "Nome",
        validators=[DataRequired(message="Nome é obrigatório"), Length(max=80)],
        render_kw={"placeholder": "Ex: 30/60/90 dias"}
    )
    forma_pagamento_id = SelectField(
        "Forma de Pagamento",
        coerce=int,
        validators=[DataRequired(message="Selecione a forma de pagamento")]
    )
    a_vista = BooleanField("Venda à Vista", default=False)
    
    num_parcelas = IntegerField(
        "Número de Parcelas",
        default=1,
        validators=[
            Optional(),
            NumberRange(min=1, max=99, message="Entre 1 e 99 parcelas")
        ],
        render_kw={"min": 1, "max": 99}
    )
    intervalo_dias = IntegerField(
        "Intervalo de Dias",
        default=0,
        validators=[
            Optional(),
            NumberRange(min=0, max=999, message="Entre 0 e 999 dias")
        ],
        render_kw={"min": 0, "max": 999}
    )
    ativo = BooleanField("Ativo", default=True)

    def gerar_parcelas(self):
        """
        Retorna lista de dicts com os dados das parcelas geradas automaticamente.
        """
        # Se for à vista, retorna a parcela única imediatamente
        if self.a_vista.data:
            return [{
                "numero": 1,
                "dias": 0,
                "percentual": 100.0000,
            }]

        # Se não for à vista, pegamos os dados (garantindo valores padrão caso venham None)
        n = self.num_parcelas.data or 1
        intervalo = self.intervalo_dias.data or 0
        
        percentual_base = round(100 / n, 4)
        parcelas = []

        for i in range(1, n + 1):
            if i == n:
                percentual = round(100 - percentual_base * (n - 1), 4)
            else:
                percentual = percentual_base

            parcelas.append({
                "numero": i,
                "dias": intervalo * i,
                "percentual": percentual,
            })

        return parcelas
