from datetime import datetime, timedelta
from flask import Flask, session, redirect, url_for, flash, render_template
from flask_login import logout_user, current_user
from config import Config
from app.extensions import db, login_manager, migrate, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    # ── Timeout de sessão por inatividade ─────────────────────────────────────
    @app.before_request
    def check_session_timeout():
        if current_user.is_authenticated:
            last = session.get('_last_active')
            timeout = app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(minutes=30))
            if last:
                elapsed = datetime.now() - datetime.fromisoformat(last)
                if elapsed > timeout:
                    logout_user()
                    session.clear()
                    flash('Sua sessão expirou por inatividade. Faça login novamente.', 'warning')
                    return redirect(url_for('auth.login'))
            session['_last_active'] = datetime.now().isoformat()

    # ── Headers de segurança HTTP ─────────────────────────────────────────────
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.employee import bp as employee_bp
    app.register_blueprint(employee_bp)

    from app.coordinator import bp as coordinator_bp
    app.register_blueprint(coordinator_bp)

    from app.security import bp as security_bp
    app.register_blueprint(security_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp)

    from app.profile import bp as profile_bp
    app.register_blueprint(profile_bp)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html', title='Acesso Negado'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html', title='Página não encontrada'), 404

    return app


from app import models  # noqa: E402, F401
