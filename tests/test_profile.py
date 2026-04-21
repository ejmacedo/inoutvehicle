"""Testes de troca de senha pelo próprio usuário."""
from tests.conftest import login
from app.models import User
from app.extensions import db


class TestTrocarSenha:
    def test_pagina_carrega_para_funcionario(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/conta/trocar-senha')
        assert r.status_code == 200
        assert b'Trocar Senha' in r.data

    def test_pagina_carrega_para_admin(self, client, admin):
        login(client, 'admin_user')
        r = client.get('/conta/trocar-senha')
        assert r.status_code == 200

    def test_pagina_carrega_para_coordenador(self, client, coordinator):
        login(client, 'coord_user')
        r = client.get('/conta/trocar-senha')
        assert r.status_code == 200

    def test_portaria_nao_acessa(self, client, security_user):
        login(client, 'security_user')
        r = client.get('/conta/trocar-senha', follow_redirects=True)
        assert b'permiss' in r.data.lower()

    def test_trocar_senha_valida(self, client, app, employee):
        login(client, 'emp_user')
        r = client.post('/conta/trocar-senha', data={
            'current_password': 'senha123',
            'new_password': 'novaSenha456',
            'new_password2': 'novaSenha456',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'sucesso' in r.data.lower()
        with app.app_context():
            u = db.session.get(User, employee)
            assert u.check_password('novaSenha456')
            assert not u.check_password('senha123')

    def test_senha_atual_errada(self, client, employee):
        login(client, 'emp_user')
        r = client.post('/conta/trocar-senha', data={
            'current_password': 'senhaErrada',
            'new_password': 'novaSenha456',
            'new_password2': 'novaSenha456',
        }, follow_redirects=True)
        assert b'incorreta' in r.data.lower()

    def test_senhas_novas_diferentes(self, client, employee):
        login(client, 'emp_user')
        r = client.post('/conta/trocar-senha', data={
            'current_password': 'senha123',
            'new_password': 'novaSenha456',
            'new_password2': 'outraSenha789',
        }, follow_redirects=True)
        assert b'coincidem' in r.data.lower() or b'Trocar Senha' in r.data

    def test_nova_senha_muito_curta(self, client, employee):
        login(client, 'emp_user')
        r = client.post('/conta/trocar-senha', data={
            'current_password': 'senha123',
            'new_password': '123',
            'new_password2': '123',
        }, follow_redirects=True)
        assert b'Trocar Senha' in r.data   # permanece na página

    def test_sem_login_redireciona(self, client):
        r = client.get('/conta/trocar-senha', follow_redirects=True)
        assert b'Login' in r.data
