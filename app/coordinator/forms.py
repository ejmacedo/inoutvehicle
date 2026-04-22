from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, TextAreaField,
                     BooleanField, SubmitField)
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo
from app.validators import strong_password


class ApproveForm(FlaskForm):
    """Formulário de aprovação — permite trocar o veículo na hora."""
    vehicle_id = SelectField('Veículo Aprovado', coerce=int,
                             validators=[DataRequired(message='Selecione um veículo.')])
    notes = TextAreaField('Observação (opcional)', validators=[Optional()])
    submit = SubmitField('Aprovar')


class RejectForm(FlaskForm):
    notes = TextAreaField('Motivo da Recusa', validators=[
        DataRequired(message='Informe o motivo da recusa.'),
    ])
    submit = SubmitField('Recusar')


class DriverReservationForm(FlaskForm):
    driver_id = SelectField('Motorista', coerce=int,
                            validators=[DataRequired(message='Selecione um motorista.')])
    vehicle_id = SelectField('Veículo', coerce=int,
                             validators=[DataRequired(message='Selecione um veículo.')])
    departure_datetime = DateTimeLocalField(
        'Data e Hora de Saída',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message='Informe a data e hora de saída.')],
    )
    expected_return_datetime = DateTimeLocalField(
        'Previsão de Retorno',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message='Informe a previsão de retorno.')],
    )
    reason = TextAreaField('Motivo', validators=[
        DataRequired(message='Informe o motivo.'),
        Length(min=5, max=500, message='O motivo deve ter entre 5 e 500 caracteres.'),
    ])
    submit = SubmitField('Criar Reserva')


class CoordinatorEditUserForm(FlaskForm):
    """Edição de funcionário ou motorista pelo coordenador."""
    full_name = StringField('Nome Completo', validators=[
        DataRequired(message='O nome é obrigatório.'),
        Length(max=140),
    ])
    username = StringField('Usuário', validators=[
        DataRequired(message='O usuário é obrigatório.'),
        Length(min=2, max=64),
    ])
    email = StringField('E-mail', validators=[
        DataRequired(message='O e-mail é obrigatório.'),
        Email(message='Informe um e-mail válido.'),
    ])
    password = PasswordField('Nova Senha (deixe em branco para não alterar)', validators=[
        Optional(),
        strong_password,
    ])
    password2 = PasswordField('Confirmar Nova Senha', validators=[
        EqualTo('password', message='As senhas não coincidem.'),
    ])
    is_active = BooleanField('Ativo')
    submit = SubmitField('Salvar')

    def __init__(self, original_user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_user = original_user


class CoordinatorCreateDriverForm(FlaskForm):
    full_name = StringField('Nome Completo', validators=[
        DataRequired(message='O nome é obrigatório.'),
        Length(max=140),
    ])
    username = StringField('Usuário', validators=[
        DataRequired(message='O usuário é obrigatório.'),
        Length(min=2, max=64),
    ])
    email = StringField('E-mail', validators=[
        DataRequired(message='O e-mail é obrigatório.'),
        Email(message='Informe um e-mail válido.'),
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='A senha é obrigatória.'),
        strong_password,
    ])
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirme a senha.'),
        EqualTo('password', message='As senhas não coincidem.'),
    ])
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Cadastrar Motorista')
