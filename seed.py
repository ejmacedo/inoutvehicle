"""
Inicializa o banco de dados e cria o usuário root.

Uso:
    python seed.py           → cria tabelas (não destrói dados existentes)
    python seed.py --reset   → DROP ALL + recria (⚠ apaga todos os dados)
"""
import sys
from app import create_app
from app.extensions import db
from app.models import User, Role

app = create_app()

with app.app_context():
    if '--reset' in sys.argv:
        print('⚠  Apagando banco de dados...')
        db.drop_all()

    db.create_all()
    print('Tabelas criadas/verificadas com sucesso.')

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
        print('Usuário root criado  →  login: root  /  senha: 1234')
    else:
        print('Usuário root já existe.')
