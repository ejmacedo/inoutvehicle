"""Run once to initialize the database and create the root admin user."""
from app import create_app
from app.extensions import db
from app.models import User, Role

app = create_app()

with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='root').first():
        root = User(
            username='root',
            email='root@empresa.com',
            full_name='Administrador',
            role=Role.ADMIN,
            is_active=True,
        )
        root.set_password('1234')
        db.session.add(root)
        db.session.commit()
        print('Usuário root criado com sucesso.')
    else:
        print('Usuário root já existe.')

    print('Banco de dados inicializado.')
