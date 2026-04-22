"""
Inicializa o banco de dados e cria o usuário root + dados de teste.

Uso:
    python seed.py           → cria tabelas, migra colunas e garante dados de teste
    python seed.py --reset   → DROP ALL + recria (⚠ apaga todos os dados)
"""
import sys
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models import User, Vehicle, Role

app = create_app()


def _column_exists(conn, table, column):
    result = conn.execute(text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result)


def _migrate_columns(conn):
    """Adiciona colunas novas em tabelas existentes sem apagar dados (v0.4)."""
    alterations = [
        ('vehicle_requests', 'odometer_return', 'INTEGER'),
        ('vehicle_requests', 'portaria_obs',    'TEXT'),
    ]
    for table, column, col_type in alterations:
        if not _column_exists(conn, table, column):
            conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))
            print(f'  Coluna adicionada: {table}.{column}')


def _get_or_create_user(username, email, full_name, role, password='Senha1234', is_active=True):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, email=email, full_name=full_name,
                    role=role, is_active=is_active)
        user.set_password(password)
        db.session.add(user)
        print(f'  Criado: [{role:12}] {full_name}  →  login: {username} / senha: {password}')
    return user


def _get_or_create_vehicle(plate, name, model):
    vehicle = Vehicle.query.filter_by(plate=plate).first()
    if not vehicle:
        vehicle = Vehicle(plate=plate, name=name, model=model, is_active=True)
        db.session.add(vehicle)
        print(f'  Veículo criado: {name} ({plate})')
    return vehicle


with app.app_context():
    if '--reset' in sys.argv:
        print('⚠  Apagando banco de dados...')
        db.drop_all()

    db.create_all()
    print('Tabelas criadas/verificadas com sucesso.')

    with db.engine.connect() as conn:
        _migrate_columns(conn)
        conn.commit()

    print('\n── Usuários ─────────────────────────────────────')

    # Admin
    root = _get_or_create_user('root', 'root@empresa.com', 'Administrador', Role.ADMIN)

    # Coordenadores
    coord1 = _get_or_create_user('carlos.lima',    'carlos.lima@empresa.com',    'Carlos Lima',    Role.COORDINATOR)
    coord2 = _get_or_create_user('fernanda.souza', 'fernanda.souza@empresa.com', 'Fernanda Souza', Role.COORDINATOR)

    # Funcionários
    emp1 = _get_or_create_user('eduardo.macedo',   'eduardo.macedo@empresa.com',   'Eduardo Macedo',   Role.EMPLOYEE)
    emp2 = _get_or_create_user('matheus.henrique', 'matheus.henrique@empresa.com', 'Matheus Henrique', Role.EMPLOYEE)

    # Motoristas
    drv1 = _get_or_create_user('joao.silva',    'joao.silva@empresa.com',    'João Silva',    Role.DRIVER)
    drv2 = _get_or_create_user('pedro.alves',   'pedro.alves@empresa.com',   'Pedro Alves',   Role.DRIVER)
    drv3 = _get_or_create_user('lucas.pereira', 'lucas.pereira@empresa.com', 'Lucas Pereira', Role.DRIVER)

    # Portaria
    _get_or_create_user('portaria', 'portaria@empresa.com', 'Portaria', Role.SECURITY)

    db.session.flush()

    # Vínculos coordenador → funcionário / motorista
    for emp in [emp1, emp2]:
        if coord1 not in emp.coordinators:
            emp.coordinators.append(coord1)
    for drv in [drv1, drv2, drv3]:
        if coord1 not in drv.coordinators:
            drv.coordinators.append(coord1)
        if coord2 not in drv.coordinators:
            drv.coordinators.append(coord2)

    db.session.commit()

    print('\n── Veículos ─────────────────────────────────────')
    _get_or_create_vehicle('ABC-1234', 'Gol Prata',    'Volkswagen Gol')
    _get_or_create_vehicle('DEF-5678', 'Uno Branco',   'Fiat Uno')
    _get_or_create_vehicle('GHI-9012', 'HB20 Preto',   'Hyundai HB20')
    _get_or_create_vehicle('JKL-3456', 'Strada Prata', 'Fiat Strada')
    _get_or_create_vehicle('MNO-7890', 'S10 Branca',   'Chevrolet S10')
    db.session.commit()

    print('\n── Resumo de logins ──────────────────────────────')
    print('  Todos os usuários abaixo usam senha: Senha1234')
    print()
    print('  Perfil       | Usuário')
    print('  -------------|---------------------')
    print('  Admin        | root')
    print('  Coordenador  | carlos.lima')
    print('  Coordenador  | fernanda.souza')
    print('  Funcionário  | eduardo.macedo')
    print('  Funcionário  | matheus.henrique')
    print('  Motorista    | joao.silva')
    print('  Motorista    | pedro.alves')
    print('  Motorista    | lucas.pereira')
    print('  Portaria     | portaria')
    print()
