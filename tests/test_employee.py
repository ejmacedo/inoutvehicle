"""Testes do painel de funcionário: dashboard e nova solicitação."""
from datetime import datetime, timedelta
from tests.conftest import login, make_dt


class TestEmployeeDashboard:
    def test_dashboard_carrega(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/funcionario/dashboard')
        assert r.status_code == 200
        assert b'Minhas Solicita' in r.data

    def test_dashboard_exibe_solicitacoes(self, client, employee, pending_request):
        login(client, 'emp_user')
        r = client.get('/funcionario/dashboard')
        assert b'Pendente' in r.data

    def test_coordenador_nao_acessa_dashboard_funcionario(self, client, coordinator):
        login(client, 'coord_user')
        r = client.get('/funcionario/dashboard', follow_redirects=True)
        assert r.status_code == 403

    def test_admin_nao_acessa_dashboard_funcionario(self, client, admin):
        login(client, 'admin_user')
        r = client.get('/funcionario/dashboard', follow_redirects=True)
        assert r.status_code == 403


class TestNovasolicitacao:
    def test_pagina_nova_solicitacao_carrega(self, client, employee, vehicle):
        login(client, 'emp_user')
        r = client.get('/funcionario/solicitar')
        assert r.status_code == 200
        assert b'Solicitar Ve' in r.data

    def test_solicitacao_valida_cria_registro(self, client, app, employee, vehicle):
        login(client, 'emp_user')
        r = client.post('/funcionario/solicitar', data={
            'full_name': 'Emp User',
            'vehicle_id': vehicle,
            'departure_datetime': make_dt(2),
            'expected_return_datetime': make_dt(6),
            'reason': 'Visita técnica ao cliente para instalação de equipamentos.',
            'returns_to_company': 'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'Aguardando aprova' in r.data

    def test_retorno_antes_da_saida_rejeitado(self, client, employee, vehicle):
        login(client, 'emp_user')
        r = client.post('/funcionario/solicitar', data={
            'full_name': 'Emp User',
            'vehicle_id': vehicle,
            'departure_datetime': make_dt(6),
            'expected_return_datetime': make_dt(2),  # anterior à saída
            'reason': 'Visita técnica ao cliente para instalação de equipamentos.',
            'returns_to_company': 'y',
        }, follow_redirects=True)
        assert b'posterior' in r.data.lower()

    def test_veiculo_indisponivel_bloqueado(self, client, app, employee, vehicle, approved_request):
        """Veículo já aprovado (sem retorno registrado) deve ser bloqueado."""
        login(client, 'emp_user')
        r = client.post('/funcionario/solicitar', data={
            'full_name': 'Emp User',
            'vehicle_id': vehicle,
            'departure_datetime': make_dt(2),
            'expected_return_datetime': make_dt(8),
            'reason': 'Visita técnica ao cliente para instalação de equipamentos.',
            'returns_to_company': 'y',
        }, follow_redirects=True)
        assert b'indispon' in r.data.lower()

    def test_motivo_curto_rejeitado(self, client, employee, vehicle):
        login(client, 'emp_user')
        r = client.post('/funcionario/solicitar', data={
            'full_name': 'Emp User',
            'vehicle_id': vehicle,
            'departure_datetime': make_dt(2),
            'expected_return_datetime': make_dt(6),
            'reason': 'Ok',   # menos de 5 chars
            'returns_to_company': 'y',
        }, follow_redirects=True)
        # Formulário deve rejeitar e permanecer na página
        assert b'Solicitar Ve' in r.data
