from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_user, logout_user
from urllib.parse import urlsplit
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.auth import bp
from app.auth.forms import LoginForm, PasswordResetRequestForm, PasswordResetForm
from app.models import User
from app.extensions import db
from app.email_utils import send_email
from app.audit import log_action
from app import security_utils


def _make_token(email: str) -> str:
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset-salt')


def _verify_token(token: str, max_age: int = 3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return s.loads(token, salt='password-reset-salt', max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    error = None
    ip = request.remote_addr

    if form.validate_on_submit():
        if security_utils.is_blocked(ip):
            mins = security_utils.remaining_lockout_minutes(ip)
            error = (f'Acesso bloqueado por excesso de tentativas. '
                     f'Tente novamente em {mins} minuto(s).')
            log_action('LOGIN_BLOQUEADO',
                       f"IP {ip} bloqueado — tentativa para '{form.username.data}'.")
        else:
            user = db.session.scalar(
                db.select(User).where(User.username == form.username.data)
            )
            if user is None or not user.check_password(form.password.data):
                security_utils.record_failure(ip)
                remaining = security_utils.MAX_ATTEMPTS - len(security_utils._attempts[ip])
                error = 'Usuário ou senha inválidos. Verifique suas credenciais.'
                if remaining <= 2:
                    error += f' ({remaining} tentativa(s) restante(s) antes do bloqueio)'
                log_action('LOGIN_FAIL',
                           f"Falha de login para '{form.username.data}' (IP: {ip}).")
            elif not user.is_active:
                error = 'Sua conta está inativa. Entre em contato com o administrador.'
                log_action('LOGIN_FAIL',
                           f"Login recusado — conta inativa: '{user.username}' (IP: {ip}).")
            else:
                security_utils.clear(ip)
                login_user(user, remember=form.remember_me.data)
                log_action('LOGIN_OK', f"Login: '{user.username}' (IP: {ip}).")
                next_page = request.args.get('next')
                if not next_page or urlsplit(next_page).netloc != '':
                    next_page = url_for('main.index')
                return redirect(next_page)

    return render_template('auth/login.html', title='Login', form=form, error=error)


@bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        log_action('LOGOUT', f"Logout: '{current_user.username}'.")
    logout_user()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/recuperar-senha', methods=['GET', 'POST'])
def password_reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.email == form.email.data))
        flash('Se este e-mail estiver cadastrado, você receberá um link em breve.', 'info')
        if user:
            token = _make_token(user.email)
            reset_url = url_for('auth.password_reset', token=token, _external=True)
            html = render_template('email/password_reset.html', user=user, reset_url=reset_url)
            send_email(subject='[InOut] Redefinição de senha',
                       recipients=[user.email], html_body=html)
        return redirect(url_for('auth.login'))
    return render_template('auth/password_reset_request.html',
                           title='Recuperar Senha', form=form)


@bp.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    email = _verify_token(token)
    if not email:
        flash('O link é inválido ou expirou. Solicite um novo.', 'danger')
        return redirect(url_for('auth.password_reset_request'))
    user = db.session.scalar(db.select(User).where(User.email == email))
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('auth.login'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        log_action('SENHA_REDEFINIDA', f"Senha de '{user.username}' redefinida via e-mail.")
        flash('Senha redefinida! Faça login com a nova senha.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/password_reset.html', title='Redefinir Senha', form=form)
