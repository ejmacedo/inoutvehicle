from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, SelectMultipleField,
                     BooleanField, SubmitField)
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo
from app.validators import strong_password


class UserForm(FlaskForm):
    username = StringField('Usuário', validators=[
        DataRequired(message='O nome de usuário é obrigatório.'),
        Length(min=2, max=64, message='O usuário deve ter entre 2 e 64 caracteres.'),
    ])
    email = StringField('E-mail', validators=[
        DataRequired(message='O e-mail é obrigatório.'),
        Email(message='Informe um endereço de e-mail válido.'),
        Length(max=120, message='O e-mail deve ter no máximo 120 caracteres.'),
    ])
    full_name = StringField('Nome Completo', validators=[
        DataRequired(message='O nome completo é obrigatório.'),
        Length(max=140, message='O nome deve ter no máximo 140 caracteres.'),
    ])
    role = SelectField('Perfil', choices=[
        ('employee', 'Funcionário'),
        ('coordinator', 'Coordenador'),
        ('security', 'Portaria'),
        ('admin', 'Administrador'),
        ('driver', 'Motorista'),
    ], validators=[DataRequired(message='Selecione um perfil.')])
    coordinator_ids = SelectMultipleField(
        'Coordenadores Responsáveis',
        coerce=int,
        validators=[Optional()],
        description='Marque um ou mais coordenadores responsáveis por este funcionário.',
    )
    password = PasswordField('Senha', validators=[
        DataRequired(message='A senha é obrigatória.'),
        strong_password,
    ])
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirme a senha.'),
        EqualTo('password', message='As senhas não coincidem.'),
    ])
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')


class EditUserForm(FlaskForm):
    username = StringField('Usuário', validators=[
        DataRequired(message='O nome de usuário é obrigatório.'),
        Length(min=2, max=64, message='O usuário deve ter entre 2 e 64 caracteres.'),
    ])
    email = StringField('E-mail', validators=[
        DataRequired(message='O e-mail é obrigatório.'),
        Email(message='Informe um endereço de e-mail válido.'),
        Length(max=120, message='O e-mail deve ter no máximo 120 caracteres.'),
    ])
    full_name = StringField('Nome Completo', validators=[
        DataRequired(message='O nome completo é obrigatório.'),
        Length(max=140, message='O nome deve ter no máximo 140 caracteres.'),
    ])
    role = SelectField('Perfil', choices=[
        ('employee', 'Funcionário'),
        ('coordinator', 'Coordenador'),
        ('security', 'Portaria'),
        ('admin', 'Administrador'),
        ('driver', 'Motorista'),
    ], validators=[DataRequired(message='Selecione um perfil.')])
    coordinator_ids = SelectMultipleField(
        'Coordenadores Responsáveis',
        coerce=int,
        validators=[Optional()],
        description='Marque um ou mais coordenadores responsáveis por este funcionário.',
    )
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


class VehicleForm(FlaskForm):
    name = StringField('Nome', validators=[
        DataRequired(message='O nome do veículo é obrigatório.'),
        Length(max=100, message='O nome deve ter no máximo 100 caracteres.'),
    ])
    plate = StringField('Placa', validators=[
        DataRequired(message='A placa é obrigatória.'),
        Length(max=20, message='A placa deve ter no máximo 20 caracteres.'),
    ])
    model = StringField('Modelo', validators=[
        DataRequired(message='O modelo é obrigatório.'),
        Length(max=100, message='O modelo deve ter no máximo 100 caracteres.'),
    ])
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')
