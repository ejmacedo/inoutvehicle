"""Testes de autenticação: login, logout, acesso sem login."""
from tests.conftest import login, logout


class TestLogin:
    def test_login_page_carrega(self, client):
        r = client.get('/login')
        assert r.status_code == 200
        assert b'Login' in r.data

    def test_login_valido_redireciona(self, client, employee):
        r = login(client, 'emp_user')
        assert r.status_code == 200
        # Após login, funcionário vai para o dashboard de funcionário
        assert b'Minhas Solicita' in r.data

    def test_login_valido_admin(self, client, admin):
        r = login(client, 'admin_user')
        assert r.status_code == 200
        assert b'Painel Admin' in r.data

    def test_login_valido_coordenador(self, client, coordinator):
        r = login(client, 'coord_user')
        assert r.status_code == 200
        assert b'Painel do Coordenador' in r.data

    def test_login_valido_portaria(self, client, security_user):
        r = login(client, 'security_user')
        assert r.status_code == 200
        assert b'Portaria' in r.data

    def test_login_senha_errada(self, client, employee):
        r = client.post('/login', data={'username': 'emp_user', 'password': 'errada'},
                        follow_redirects=True)
        assert b'inv' in r.data.lower()   # "inválidos"

    def test_login_usuario_inexistente(self, client):
        r = client.post('/login', data={'username': 'naoexiste', 'password': 'qualquer'},
                        follow_redirects=True)
        assert b'inv' in r.data.lower()

    def test_login_usuario_inativo(self, client, inactive_user):
        r = client.post('/login', data={'username': 'inactive_user', 'password': 'Senha123'},
                        follow_redirects=True)
        assert b'inativa' in r.data.lower()

    def test_logout(self, client, employee):
        login(client, 'emp_user')
        r = logout(client)
        assert r.status_code == 200
        assert b'Login' in r.data

    def test_acesso_sem_login_redireciona(self, client):
        r = client.get('/funcionario/dashboard', follow_redirects=True)
        assert b'Login' in r.data

    def test_usuario_ja_logado_nao_ve_login(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/login', follow_redirects=True)
        # Redireciona para o dashboard, não mostra formulário de login
        assert b'Minhas Solicita' in r.data
