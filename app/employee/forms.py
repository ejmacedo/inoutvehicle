from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Length


class VehicleRequestForm(FlaskForm):
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(max=140)])
    vehicle_id = SelectField('Veículo', coerce=int, validators=[DataRequired()])
    departure_datetime = DateTimeLocalField(
        'Data e Hora de Saída',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()]
    )
    expected_return_datetime = DateTimeLocalField(
        'Previsão de Chegada',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()]
    )
    reason = TextAreaField('Motivo da Saída', validators=[DataRequired(), Length(min=5, max=500)])
    returns_to_company = BooleanField('Retorna para a empresa?')
    submit = SubmitField('Solicitar Saída')
