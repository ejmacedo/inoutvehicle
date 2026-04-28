from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.privacy import bp
from app.extensions import db
from app.audit import log_action


@bp.route('/privacidade')
def policy():
    return render_template('privacy/policy.html', title='Política de Privacidade')


@bp.route('/consentimento', methods=['GET', 'POST'])
@login_required
def consent():
    if current_user.consent_accepted_at is not None:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        if request.form.get('aceito') == '1':
            current_user.consent_accepted_at = datetime.now(timezone.utc)
            db.session.commit()
            log_action('CONSENTIMENTO_ACEITO',
                       f"Usuário '{current_user.username}' aceitou a Política de Privacidade.")
            flash('Bem-vindo! Seu consentimento foi registrado.', 'success')
            return redirect(url_for('main.index'))
        flash('É necessário aceitar a Política de Privacidade para usar o sistema.', 'warning')

    return render_template('privacy/consent.html', title='Aceite de Privacidade')
