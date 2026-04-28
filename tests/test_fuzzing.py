"""
Fuzzing tests: "socando" dados que o campo não foi feito para aceitar.
Dados aleatórios, injeções, strings gigantes, tipos errados, Unicode.
O sistema nunca pode retornar 500 — deve rejeitar com 400 ou reexibir o form.
"""
import pytest
from tests.conftest import login, make_dt


# ── Payloads de fuzzing ───────────────────────────────────────────────────────

SQL_INJECTION = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "1; SELECT * FROM users--",
    "' UNION SELECT username, password FROM users--",
    "admin'--",
    "1' AND SLEEP(5)--",
    '" OR ""="',
]

XSS = [
    '<script>alert("xss")</script>',
    '"><img src=x onerror=alert(1)>',
    "javascript:alert('xss')",
    '<svg onload=alert(1)>',
    '{{7*7}}',          # SSTI (Jinja template injection attempt)
    '{%import os%}',
    '${7*7}',           # EL injection
]

BOUNDARY = [
    '',                          # vazio
    ' ',                         # só espaço
    '   ',                       # vários espaços
    'a' * 10_000,                # string enorme
    'a' * 300,                   # acima do max length esperado
    '\x00',                      # null byte
    '\x00' * 50,                 # null bytes em sequência
    '\n\r\t\x08',                # caracteres de controle
    '%s%s%s%s%s',                # format string
    '../../../../etc/passwd',    # path traversal
    'None',                      # string "None"
    'null',                      # string "null"
    'undefined',
    'true', 'false',
    '0', '-1', '-999999',
    '9' * 20,                    # número gigante como string
]

UNICODE = [
    '🚀🔥💀' * 50,
    'Ação de ré com açúcar ñoño',
    '日本語テスト',
    'عربي',
    '‮',                    # right-to-left override
    '￿',
    'à' * 200,
]

ALL_PAYLOADS = SQL_INJECTION + XSS + BOUNDARY + UNICODE


def never_500(r):
    assert r.status_code != 500, (
        f"O sistema retornou 500:\n{r.data[:600].decode(errors='replace')}"
    )


# ── Login com dados maliciosos ────────────────────────────────────────────────

class TestFuzzingLogin:
    @pytest.mark.parametrize('payload', ALL_PAYLOADS)
    def test_username_malicioso(self, client, payload):
        r = client.post('/login', data={
            'username': payload,
            'password': 'qualquer',
        }, follow_redirects=True)
        never_500(r)

    @pytest.mark.parametrize('payload', ALL_PAYLOADS)
    def test_password_maliciosa(self, client, payload):
        r = client.post('/login', data={
            'username': 'qualquer',
            'password': payload,
        }, follow_redirects=True)
        never_500(r)

    def test_login_sem_dados(self, client):
        r = client.post('/login', data={}, follow_redirects=True)
        never_500(r)

    def test_login_campos_extras(self, client):
        r = client.post('/login', data={
            'username': 'root',
            'password': 'Senha1234',
            'role': 'admin',
            'is_admin': 'true',
            'extra_field': '<script>alert(1)</script>',
        }, follow_redirects=True)
        never_500(r)


# ── Criação de usuário (admin) com dados maliciosos ───────────────────────────

class TestFuzzingCriarUsuario:
    @pytest.mark.parametrize('campo,valor', [
        ('username', "' OR 1=1--"),
        ('username', '<script>alert(1)</script>'),
        ('username', 'a' * 300),
        ('username', ''),
        ('email', "nao-é-email"),
        ('email', "' OR 1=1--@test.com"),
        ('email', 'a' * 300 + '@test.com'),
        ('email', '@'),
        ('full_name', 'a' * 500),
        ('full_name', '<script>xss</script>'),
        ('full_name', ''),
        ('role', 'superadmin'),
        ('role', "' OR '1'='1"),
        ('role', ''),
        ('role', 'admin; DROP TABLE users'),
        ('password', '123'),              # senha fraca (deve rejeitar)
        ('password', 'a' * 500),
        ('password', ''),
    ])
    def test_campo_invalido_nao_causa_500(self, client, admin, campo, valor):
        login(client, 'admin_user')
        dados = {
            'username': 'novo_fuzz',
            'email': 'fuzz@test.com',
            'full_name': 'Fuzz User',
            'role': 'employee',
            'password': 'Senha123',
            'password2': 'Senha123',
            'is_active': 'y',
        }
        dados[campo] = valor
        r = client.post('/admin/usuarios/novo', data=dados, follow_redirects=True)
        never_500(r)


# ── Criação de veículo com dados maliciosos ───────────────────────────────────

class TestFuzzingCriarVeiculo:
    @pytest.mark.parametrize('payload', SQL_INJECTION + XSS + [
        'a' * 500, '', ' ', '\x00', '{{7*7}}',
    ])
    def test_nome_malicioso(self, client, admin, payload):
        login(client, 'admin_user')
        r = client.post('/admin/veiculos/novo', data={
            'name': payload,
            'plate': 'FUZ-9999',
            'model': 'Modelo Teste',
            'is_active': 'y',
        }, follow_redirects=True)
        never_500(r)

    @pytest.mark.parametrize('payload', SQL_INJECTION + [
        'a' * 100, '', ' ', 'ABC-123; DROP TABLE vehicles',
        '../../etc', "' OR 1=1",
    ])
    def test_placa_maliciosa(self, client, admin, payload):
        login(client, 'admin_user')
        r = client.post('/admin/veiculos/novo', data={
            'name': 'Carro Fuzz',
            'plate': payload,
            'model': 'Modelo',
            'is_active': 'y',
        }, follow_redirects=True)
        never_500(r)


# ── Solicitação de veículo com dados maliciosos ───────────────────────────────

class TestFuzzingSolicitacao:
    @pytest.mark.parametrize('payload', SQL_INJECTION + XSS + [
        'a' * 5000, '', ' ', '\x00', '{{7*7}}', '🚀' * 100,
    ])
    def test_motivo_malicioso(self, client, employee, vehicle, payload):
        login(client, 'emp_user')
        r = client.post('/funcionario/solicitar', data={
            'vehicle_id': str(vehicle),
            'departure_datetime': make_dt(2),
            'expected_return_datetime': make_dt(6),
            'reason': payload,
            'returns_to_company': 'y',
        }, follow_redirects=True)
        never_500(r)

    @pytest.mark.parametrize('vehicle_id', [
        '0', '-1', '99999', 'abc', "' OR 1=1", '',
        '<script>', '9' * 15, 'null', 'undefined',
    ])
    def test_vehicle_id_invalido(self, client, employee, vehicle_id):
        login(client, 'emp_user')
        r = client.post('/funcionario/solicitar', data={
            'vehicle_id': vehicle_id,
            'departure_datetime': make_dt(2),
            'expected_return_datetime': make_dt(6),
            'reason': 'Teste',
            'returns_to_company': 'y',
        }, follow_redirects=True)
        never_500(r)

    @pytest.mark.parametrize('dt_value', [
        '', 'nao-é-data', '2020-13-45T99:99', '9999-99-99T99:99',
        "' OR 1=1", '<script>', '0', '-1', 'null', '99999999999999',
    ])
    def test_data_invalida(self, client, employee, vehicle, dt_value):
        login(client, 'emp_user')
        r = client.post('/funcionario/solicitar', data={
            'vehicle_id': str(vehicle),
            'departure_datetime': dt_value,
            'expected_return_datetime': make_dt(6),
            'reason': 'Teste',
            'returns_to_company': 'y',
        }, follow_redirects=True)
        never_500(r)


# ── Troca de senha com dados maliciosos ──────────────────────────────────────

class TestFuzzingTrocarSenha:
    @pytest.mark.parametrize('payload', SQL_INJECTION + XSS + [
        'a' * 2000, '', ' ', '\x00', '{{7*7}}', '123', 'abc',
    ])
    def test_senha_atual_maliciosa(self, client, employee, payload):
        login(client, 'emp_user')
        r = client.post('/conta/trocar-senha', data={
            'current_password': payload,
            'new_password': 'NovaSenha123',
            'new_password2': 'NovaSenha123',
        }, follow_redirects=True)
        never_500(r)

    @pytest.mark.parametrize('payload', SQL_INJECTION + XSS + [
        'a' * 2000, '', ' ', '\x00', '123', 'semMaiuscula1',
    ])
    def test_nova_senha_maliciosa(self, client, employee, payload):
        login(client, 'emp_user')
        r = client.post('/conta/trocar-senha', data={
            'current_password': 'Senha123',
            'new_password': payload,
            'new_password2': payload,
        }, follow_redirects=True)
        never_500(r)


# ── Portaria com odômetro malicioso ──────────────────────────────────────────

class TestFuzzingPortaria:
    @pytest.mark.parametrize('odometro', [
        '-1', '-999999', '0', '9' * 15, 'abc', "' OR 1=1",
        '', 'null', 'NaN', '1.5', '1,5', '<script>', '{{7*7}}',
    ])
    def test_odometro_invalido_saida(self, client, security_user, approved_request, odometro):
        login(client, 'security_user')
        r = client.post(f'/portaria/solicitacao/{approved_request}/saiu', data={
            'odometer': odometro,
        }, follow_redirects=True)
        never_500(r)

    @pytest.mark.parametrize('obs', SQL_INJECTION + XSS + [
        'a' * 5000, '\x00' * 10, '{{7*7}}', '🚀' * 200,
    ])
    def test_observacao_maliciosa_saida(self, client, security_user, approved_request, obs):
        login(client, 'security_user')
        r = client.post(f'/portaria/solicitacao/{approved_request}/saiu', data={
            'odometer': '50000',
            'obs': obs,
        }, follow_redirects=True)
        never_500(r)


# ── Parâmetros de query string maliciosos ────────────────────────────────────

class TestFuzzingQueryString:
    @pytest.mark.parametrize('payload', SQL_INJECTION + XSS + [
        'a' * 1000, '\x00', '{{7*7}}', '🚀',
    ])
    def test_filtro_auditoria_malicioso(self, client, admin, payload):
        login(client, 'admin_user')
        r = client.get(f'/admin/auditoria?action={payload}&user={payload}&page=1')
        never_500(r)

    @pytest.mark.parametrize('page', [
        '-1', '0', '99999999', 'abc', "' OR 1=1", '',
        '<script>', 'null', '1.5',
    ])
    def test_paginacao_invalida(self, client, admin, page):
        login(client, 'admin_user')
        r = client.get(f'/admin/auditoria?page={page}')
        never_500(r)

    @pytest.mark.parametrize('payload', SQL_INJECTION + XSS + ['a' * 500, ''])
    def test_filtro_relatorios_malicioso(self, client, admin, payload):
        login(client, 'admin_user')
        r = client.get(f'/relatorios/?status={payload}&search={payload}')
        never_500(r)


# ── Campos extras / não esperados ─────────────────────────────────────────────

class TestCamposExtras:
    def test_campos_extras_no_login(self, client):
        r = client.post('/login', data={
            'username': 'root',
            'password': 'Senha1234',
            '__proto__': '{"admin":true}',
            'constructor': 'Object',
            'is_admin': '1',
            'role': 'admin',
            'id': '1',
        }, follow_redirects=True)
        never_500(r)

    def test_campos_extras_criar_usuario(self, client, admin):
        login(client, 'admin_user')
        r = client.post('/admin/usuarios/novo', data={
            'username': 'extra_test',
            'email': 'extra@test.com',
            'full_name': 'Extra Test',
            'role': 'employee',
            'password': 'Senha123',
            'password2': 'Senha123',
            'is_active': 'y',
            'id': '999',
            'is_admin': 'true',
            '__proto__': 'hack',
            'consent_accepted_at': '2000-01-01',
        }, follow_redirects=True)
        never_500(r)

    def test_campos_extras_nova_solicitacao(self, client, employee, vehicle):
        login(client, 'emp_user')
        r = client.post('/funcionario/solicitar', data={
            'vehicle_id': str(vehicle),
            'departure_datetime': make_dt(2),
            'expected_return_datetime': make_dt(6),
            'reason': 'Teste legítimo',
            'returns_to_company': 'y',
            'status': 'approved',         # tentativa de forçar aprovação
            'coordinator_notes': 'auto-aprovado',
            'employee_id': '999',
        }, follow_redirects=True)
        never_500(r)
        # Solicitação criada deve ser pending, nunca approved
        from app.models import VehicleRequest, RequestStatus
        from app.extensions import db
        vr = VehicleRequest.query.filter_by(reason='Teste legítimo').first()
        if vr:
            assert vr.status == RequestStatus.PENDING


# ── Recuperação de senha com dados maliciosos ────────────────────────────────

class TestFuzzingRecuperarSenha:
    @pytest.mark.parametrize('payload', SQL_INJECTION + XSS + [
        'a' * 500, '', 'nao@email', '<script>', '{{7*7}}',
        'root@empresa.com',  # e-mail real — deve tratar sem vazar info
    ])
    def test_email_recuperacao_invalido(self, client, payload):
        r = client.post('/recuperar-senha', data={
            'email': payload,
        }, follow_redirects=True)
        never_500(r)

    def test_token_redefinicao_invalido(self, client):
        for token in ["' OR 1=1", '<script>', 'a' * 200, '../../etc/passwd', '{{7*7}}']:
            r = client.get(f'/redefinir-senha/{token}')
            never_500(r)
            assert r.status_code in (200, 302, 404)
