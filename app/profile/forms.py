from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from app.validators import strong_password


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha Atual', validators=[
        DataRequired(message='Informe a senha atual.'),
    ])
    new_password = PasswordField('Nova Senha', validators=[
        DataRequired(message='Informe a nova senha.'),
        strong_password,
    ])
    new_password2 = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirme a nova senha.'),
        EqualTo('new_password', message='As senhas não coincidem.'),
    ])
    submit = SubmitField('Alterar Senha')
