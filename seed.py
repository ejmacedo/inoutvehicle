"""
Inicializa o banco de dados e cria o usuário root.

Uso:
    python seed.py           → cria tabelas e migra colunas novas (não destrói dados)
    python seed.py --reset   → DROP ALL + recria (⚠ apaga todos os dados)
"""
import sys
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models import User, Role

app = create_app()


def _column_exists(conn, table, column):
    result = conn.execute(text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result)


def _migrate_columns(conn):
    """Adiciona colunas novas em tabelas existentes sem apagar dados (v0.4)."""
    alterations = [
        ('vehicle_requests', 'odometer_return',  'INTEGER'),
        ('vehicle_requests', 'portaria_obs',      'TEXT'),
    ]
    for table, column, col_type in alterations:
        if not _column_exists(conn, table, column):
            conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))
            print(f'  Coluna adicionada: {table}.{column}')


with app.app_context():
    if '--reset' in sys.argv:
        print('⚠  Apagando banco de dados...')
        db.drop_all()

    db.create_all()
    print('Tabelas criadas/verificadas com sucesso.')

    with db.engine.connect() as conn:
        _migrate_columns(conn)
        conn.commit()

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
