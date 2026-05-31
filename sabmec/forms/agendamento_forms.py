from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, TimeField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

class FormAgendamento(FlaskForm):
    # SelectFields com coerce=int para lidar com IDs
    cliente_id = SelectField("Cliente", coerce=int, validators=[DataRequired(message="Selecione o cliente.")])
    veiculo_id = SelectField("Veículo", coerce=int, validators=[DataRequired(message="Selecione o veículo.")])
    
    data = DateField("Data", validators=[DataRequired(message="Informe a data.")])
    hora = TimeField("Hora", validators=[DataRequired(message="Informe a hora.")])
    
    problema_relatado = TextAreaField("Problema Relatado", validators=[Optional(), Length(max=1000)])
    observacoes = TextAreaField("Observações", validators=[Optional(), Length(max=1000)])
    
    submit = SubmitField("Salvar Agendamento")
