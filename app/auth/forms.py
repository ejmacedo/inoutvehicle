from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from app.validators import strong_password


class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[
        DataRequired(message='O usuário é obrigatório.'),
        Length(min=2, max=64, message='O usuário deve ter entre 2 e 64 caracteres.'),
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='A senha é obrigatória.'),
    ])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('E-mail', validators=[
        DataRequired(message='O e-mail é obrigatório.'),
        Email(message='Informe um endereço de e-mail válido.'),
    ])
    submit = SubmitField('Enviar link de recuperação')


class PasswordResetForm(FlaskForm):
    password = PasswordField('Nova Senha', validators=[
        DataRequired(message='A nova senha é obrigatória.'),
        strong_password,
    ])
    password2 = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirme a nova senha.'),
        EqualTo('password', message='As senhas não coincidem.'),
    ])
    submit = SubmitField('Redefinir Senha')
