import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread
from flask import current_app, render_template


def _send(app, subject, recipients, html_body):
    """Envia e-mail em background thread para não bloquear a requisição."""
    with app.app_context():
        cfg = app.config
        if not cfg.get('MAIL_SERVER') or not cfg.get('MAIL_USERNAME'):
            app.logger.warning('E-mail não configurado — notificação ignorada.')
            return
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = cfg.get('MAIL_DEFAULT_SENDER') or cfg['MAIL_USERNAME']
            msg['To'] = ', '.join(recipients)
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            server = smtplib.SMTP(cfg['MAIL_SERVER'], cfg['MAIL_PORT'])
            if cfg.get('MAIL_USE_TLS', True):
                server.starttls()
            server.login(cfg['MAIL_USERNAME'], cfg['MAIL_PASSWORD'])
            server.sendmail(msg['From'], recipients, msg.as_string())
            server.quit()
            app.logger.info(f'E-mail enviado para {recipients}')
        except Exception as exc:
            app.logger.error(f'Erro ao enviar e-mail: {exc}')


def send_email(subject, recipients, html_body):
    """Dispara envio assíncrono de e-mail."""
    app = current_app._get_current_object()
    if not recipients:
        return
    Thread(target=_send, args=(app, subject, recipients, html_body), daemon=True).start()


# ── Notificações específicas ──────────────────────────────────────────────────

def notify_coordinators_new_request(vehicle_request):
    """Avisa todos os coordenadores do funcionário sobre nova solicitação."""
    coordinators = vehicle_request.employee.coordinators
    if not coordinators:
        return
    recipients = [c.email for c in coordinators if c.email]
    html = render_template('email/new_request.html', req=vehicle_request)
    send_email(
        subject=f'[InOut] Nova solicitação de veículo — {vehicle_request.employee.full_name}',
        recipients=recipients,
        html_body=html,
    )


def notify_employee_approved(vehicle_request):
    """Avisa o funcionário que sua solicitação foi aprovada."""
    recipient = vehicle_request.employee.email
    if not recipient:
        return
    html = render_template('email/request_approved.html', req=vehicle_request)
    send_email(
        subject='[InOut] Sua solicitação de veículo foi aprovada',
        recipients=[recipient],
        html_body=html,
    )


def notify_employee_rejected(vehicle_request):
    """Avisa o funcionário que sua solicitação foi recusada."""
    recipient = vehicle_request.employee.email
    if not recipient:
        return
    html = render_template('email/request_rejected.html', req=vehicle_request)
    send_email(
        subject='[InOut] Sua solicitação de veículo foi recusada',
        recipients=[recipient],
        html_body=html,
    )
