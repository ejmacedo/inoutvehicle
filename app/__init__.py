from flask import Flask
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

    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html', title='Acesso Negado'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html', title='Página não encontrada'), 404

    return app


from app import models  # noqa: E402, F401
