"""Testes do painel de administrador: usuários e veículos."""
from tests.conftest import login
from app.models import User, Vehicle, Role
from app.extensions import db


class TestAdminDashboard:
    def test_dashboard_carrega(self, client, admin):
        login(client, 'admin_user')
        r = client.get('/admin/dashboard')
        assert r.status_code == 200
        assert b'Painel Admin' in r.data

    def test_funcionario_nao_acessa_admin(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/admin/dashboard', follow_redirects=True)
        assert r.status_code == 403

    def test_coordenador_nao_acessa_admin(self, client, coordinator):
        login(client, 'coord_user')
        r = client.get('/admin/dashboard', follow_redirects=True)
        assert r.status_code == 403


class TestAdminUsuarios:
    def test_lista_usuarios(self, client, admin, employee):
        login(client, 'admin_user')
        r = client.get('/admin/usuarios')
        assert r.status_code == 200
        assert b'Emp User' in r.data

    def test_criar_usuario_valido(self, client, app, admin, coordinator):
        login(client, 'admin_user')
        r = client.post('/admin/usuarios/novo', data={
            'username': 'novo_funcionario',
            'email': 'novo_func@test.com',
            'full_name': 'Novo Funcionário',
            'role': 'employee',
            'coordinator_ids': [coordinator],
            'password': 'Senha123',
            'password2': 'Senha123',
            'is_active': 'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'criado' in r.data.lower()
        with app.app_context():
            u = User.query.filter_by(username='novo_funcionario').first()
            assert u is not None
            assert u.role == Role.EMPLOYEE

    def test_criar_usuario_duplicado_bloqueado(self, client, admin, employee):
        login(client, 'admin_user')
        r = client.post('/admin/usuarios/novo', data={
            'username': 'emp_user',   # já existe
            'email': 'outro@test.com',
            'full_name': 'Outro',
            'role': 'employee',
            'password': 'Senha123',
            'password2': 'Senha123',
            'is_active': 'y',
        }, follow_redirects=True)
        assert b'j' in r.data.lower() and b'uso' in r.data.lower()

    def test_criar_usuario_email_duplicado_bloqueado(self, client, admin, employee):
        login(client, 'admin_user')
        r = client.post('/admin/usuarios/novo', data={
            'username': 'outro_user',
            'email': 'emp_user@test.com',   # já existe
            'full_name': 'Outro',
            'role': 'employee',
            'password': 'Senha123',
            'password2': 'Senha123',
            'is_active': 'y',
        }, follow_redirects=True)
        assert b'j' in r.data.lower() and b'cadastrado' in r.data.lower()

    def test_criar_usuario_senhas_diferentes_bloqueado(self, client, admin):
        login(client, 'admin_user')
        r = client.post('/admin/usuarios/novo', data={
            'username': 'user_novo',
            'email': 'novo@test.com',
            'full_name': 'Novo',
            'role': 'employee',
            'password': 'Senha123',
            'password2': 'senhaDiferente',
            'is_active': 'y',
        }, follow_redirects=True)
        assert b'coincidem' in r.data.lower() or b'Novo Usu' in r.data

    def test_editar_usuario(self, client, app, admin, employee):
        login(client, 'admin_user')
        r = client.post(f'/admin/usuarios/{employee}/editar', data={
            'username': 'emp_user',
            'email': 'emp_user@test.com',
            'full_name': 'Emp Atualizado Admin',
            'role': 'employee',
            'password': '',
            'password2': '',
            'is_active': 'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'atualizado' in r.data.lower()
        with app.app_context():
            u = db.session.get(User, employee)
            assert u.full_name == 'Emp Atualizado Admin'

    def test_editar_usuario_com_nova_senha(self, client, app, admin, employee):
        login(client, 'admin_user')
        client.post(f'/admin/usuarios/{employee}/editar', data={
            'username': 'emp_user',
            'email': 'emp_user@test.com',
            'full_name': 'Emp User',
            'role': 'employee',
            'password': 'NovaSenha456',
            'password2': 'NovaSenha456',
            'is_active': 'y',
        }, follow_redirects=True)
        with app.app_context():
            u = db.session.get(User, employee)
            assert u.check_password('NovaSenha456')

    def test_desativar_usuario(self, client, app, admin, employee):
        login(client, 'admin_user')
        client.post(f'/admin/usuarios/{employee}/editar', data={
            'username': 'emp_user',
            'email': 'emp_user@test.com',
            'full_name': 'Emp User',
            'role': 'employee',
            'password': '',
            'password2': '',
            # is_active ausente = False (checkbox desmarcado)
        }, follow_redirects=True)
        with app.app_context():
            u = db.session.get(User, employee)
            assert u.is_active is False

    def test_criar_todos_os_perfis(self, client, app, admin):
        login(client, 'admin_user')
        for role in ('employee', 'coordinator', 'security', 'driver', 'admin'):
            r = client.post('/admin/usuarios/novo', data={
                'username': f'user_{role}',
                'email': f'user_{role}@test.com',
                'full_name': f'Usuário {role}',
                'role': role,
                'password': 'Senha123',
                'password2': 'Senha123',
                'is_active': 'y',
            }, follow_redirects=True)
            assert b'criado' in r.data.lower(), f'Falhou para perfil: {role}'


class TestAdminVeiculos:
    def test_lista_veiculos(self, client, admin, vehicle):
        login(client, 'admin_user')
        r = client.get('/admin/veiculos')
        assert r.status_code == 200
        assert b'Gol Prata' in r.data

    def test_criar_veiculo_valido(self, client, app, admin):
        login(client, 'admin_user')
        r = client.post('/admin/veiculos/novo', data={
            'name': 'Carro Novo',
            'plate': 'NEW-9999',
            'model': 'Marca Modelo',
            'is_active': 'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'cadastrado' in r.data.lower()
        with app.app_context():
            v = Vehicle.query.filter_by(plate='NEW-9999').first()
            assert v is not None

    def test_criar_veiculo_placa_duplicada_bloqueado(self, client, admin, vehicle):
        login(client, 'admin_user')
        r = client.post('/admin/veiculos/novo', data={
            'name': 'Outro Carro',
            'plate': 'TST-0001',   # placa do fixture vehicle
            'model': 'Qualquer',
            'is_active': 'y',
        }, follow_redirects=True)
        assert b'placa' in r.data.lower() or b'j' in r.data.lower()

    def test_editar_veiculo(self, client, app, admin, vehicle):
        login(client, 'admin_user')
        r = client.post(f'/admin/veiculos/{vehicle}/editar', data={
            'name': 'Gol Atualizado',
            'plate': 'TST-0001',
            'model': 'Volkswagen Gol',
            'is_active': 'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'atualizado' in r.data.lower()
        with app.app_context():
            v = db.session.get(Vehicle, vehicle)
            assert v.name == 'Gol Atualizado'

    def test_desativar_veiculo(self, client, app, admin, vehicle):
        login(client, 'admin_user')
        client.post(f'/admin/veiculos/{vehicle}/editar', data={
            'name': 'Gol Prata',
            'plate': 'TST-0001',
            'model': 'Volkswagen Gol',
            # is_active ausente = False
        }, follow_redirects=True)
        with app.app_context():
            v = db.session.get(Vehicle, vehicle)
            assert v.is_active is False

    def test_placa_salva_em_maiusculo(self, client, app, admin):
        login(client, 'admin_user')
        client.post('/admin/veiculos/novo', data={
            'name': 'Carro Minúsculo',
            'plate': 'abc-1111',
            'model': 'Modelo',
            'is_active': 'y',
        }, follow_redirects=True)
        with app.app_context():
            v = Vehicle.query.filter_by(plate='ABC-1111').first()
            assert v is not None
