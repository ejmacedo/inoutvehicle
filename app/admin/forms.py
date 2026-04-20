from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, SelectMultipleField,
                     BooleanField, SubmitField)
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError
from app.models import User


class UserForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('E-mail', validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(max=140)])
    role = SelectField('Perfil', choices=[
        ('employee', 'Funcionário'),
        ('coordinator', 'Coordenador'),
        ('security', 'Portaria'),
        ('admin', 'Administrador'),
    ], validators=[DataRequired()])
    coordinator_ids = SelectMultipleField(
        'Coordenadores Responsáveis',
        coerce=int,
        validators=[Optional()],
        description='Segure Ctrl (ou Cmd) para selecionar múltiplos',
    )
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Este nome de usuário já está em uso.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Este e-mail já está cadastrado.')


class EditUserForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('E-mail', validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(max=140)])
    role = SelectField('Perfil', choices=[
        ('employee', 'Funcionário'),
        ('coordinator', 'Coordenador'),
        ('security', 'Portaria'),
        ('admin', 'Administrador'),
    ], validators=[DataRequired()])
    coordinator_ids = SelectMultipleField(
        'Coordenadores Responsáveis',
        coerce=int,
        validators=[Optional()],
        description='Segure Ctrl (ou Cmd) para selecionar múltiplos',
    )
    password = PasswordField(
        'Nova Senha (deixe em branco para não alterar)',
        validators=[Optional(), Length(min=6)],
    )
    password2 = PasswordField('Confirmar Nova Senha', validators=[EqualTo('password')])
    is_active = BooleanField('Ativo')
    submit = SubmitField('Salvar')

    def __init__(self, original_user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_user = original_user

    def validate_username(self, field):
        if field.data != self.original_user.username:
            if User.query.filter_by(username=field.data).first():
                raise ValidationError('Este nome de usuário já está em uso.')

    def validate_email(self, field):
        if field.data != self.original_user.email:
            if User.query.filter_by(email=field.data).first():
                raise ValidationError('Este e-mail já está cadastrado.')


class VehicleForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    plate = StringField('Placa', validators=[DataRequired(), Length(max=20)])
    model = StringField('Modelo', validators=[DataRequired(), Length(max=100)])
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')
