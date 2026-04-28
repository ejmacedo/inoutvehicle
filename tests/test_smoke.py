"""
Smoke tests: toda rota registrada no sistema deve responder sem erro 5xx
para o perfil correto. Se acendeu, está de pé.
"""
import pytest
from tests.conftest import login


# ── Helpers ───────────────────────────────────────────────────────────────────

def ok(r):
    """Aceita 200, 302 (redirect após ação), 405 — nunca 5xx."""
    assert r.status_code < 500, (
        f"Rota retornou {r.status_code}:\n{r.data[:400].decode(errors='replace')}"
    )


# ── Rotas públicas (sem login) ─────────────────────────────────────────────────

class TestPublicas:
    def test_login_page(self, client):
        ok(client.get('/login'))

    def test_recuperar_senha(self, client):
        ok(client.get('/recuperar-senha'))

    def test_politica_privacidade(self, client):
        ok(client.get('/privacidade'))

    def test_rota_inexistente_404(self, client):
        r = client.get('/rota-que-nao-existe-xyz')
        assert r.status_code == 404

    def test_sem_login_redireciona(self, client):
        r = client.get('/funcionario/dashboard', follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']


# ── Admin ─────────────────────────────────────────────────────────────────────

class TestSmokeAdmin:
    def test_dashboard(self, client, admin):
        login(client, 'admin_user')
        ok(client.get('/admin/dashboard'))

    def test_lista_usuarios(self, client, admin):
        login(client, 'admin_user')
        ok(client.get('/admin/usuarios'))

    def test_form_novo_usuario(self, client, admin):
        login(client, 'admin_user')
        ok(client.get('/admin/usuarios/novo'))

    def test_editar_usuario(self, client, admin, employee):
        login(client, 'admin_user')
        ok(client.get(f'/admin/usuarios/{employee}/editar'))

    def test_lista_veiculos(self, client, admin):
        login(client, 'admin_user')
        ok(client.get('/admin/veiculos'))

    def test_form_novo_veiculo(self, client, admin):
        login(client, 'admin_user')
        ok(client.get('/admin/veiculos/novo'))

    def test_editar_veiculo(self, client, admin, vehicle):
        login(client, 'admin_user')
        ok(client.get(f'/admin/veiculos/{vehicle}/editar'))

    def test_auditoria(self, client, admin):
        login(client, 'admin_user')
        ok(client.get('/admin/auditoria'))

    def test_auditoria_com_filtros(self, client, admin):
        login(client, 'admin_user')
        ok(client.get('/admin/auditoria?action=LOGIN_OK&user=admin&page=1'))


# ── Coordenador ───────────────────────────────────────────────────────────────

class TestSmokeCoordinator:
    def test_dashboard(self, client, coordinator, employee):
        login(client, 'coord_user')
        ok(client.get('/coordenador/dashboard'))

    def test_lista_funcionarios(self, client, coordinator, employee):
        login(client, 'coord_user')
        ok(client.get('/coordenador/funcionarios'))

    def test_editar_funcionario(self, client, coordinator, employee):
        login(client, 'coord_user')
        ok(client.get(f'/coordenador/funcionarios/{employee}/editar'))

    def test_lista_motoristas(self, client, coordinator, driver):
        login(client, 'coord_user')
        ok(client.get('/coordenador/motoristas'))

    def test_form_novo_motorista(self, client, coordinator):
        login(client, 'coord_user')
        ok(client.get('/coordenador/motoristas/novo'))

    def test_editar_motorista(self, client, coordinator, driver):
        login(client, 'coord_user')
        ok(client.get(f'/coordenador/motoristas/{driver}/editar'))

    def test_lista_reservas_motorista(self, client, coordinator):
        login(client, 'coord_user')
        ok(client.get('/coordenador/reservas-motorista'))

    def test_form_nova_reserva(self, client, coordinator, driver, vehicle):
        login(client, 'coord_user')
        ok(client.get('/coordenador/reservas-motorista/nova'))


# ── Funcionário ───────────────────────────────────────────────────────────────

class TestSmokeEmployee:
    def test_dashboard(self, client, employee):
        login(client, 'emp_user')
        ok(client.get('/funcionario/dashboard'))

    def test_form_nova_solicitacao(self, client, employee, vehicle):
        login(client, 'emp_user')
        ok(client.get('/funcionario/solicitar'))


# ── Portaria ──────────────────────────────────────────────────────────────────

class TestSmokeSecurity:
    def test_dashboard(self, client, security_user):
        login(client, 'security_user')
        ok(client.get('/portaria/dashboard'))


# ── Perfil / Conta ────────────────────────────────────────────────────────────

class TestSmokePerfil:
    def test_trocar_senha(self, client, employee):
        login(client, 'emp_user')
        ok(client.get('/conta/trocar-senha'))

    def test_meus_dados(self, client, employee):
        login(client, 'emp_user')
        ok(client.get('/conta/meus-dados'))

    def test_exportar_dados(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/conta/exportar-dados')
        ok(r)
        assert r.content_type == 'application/json'

    def test_meus_dados_coordenador(self, client, coordinator):
        login(client, 'coord_user')
        ok(client.get('/conta/meus-dados'))

    def test_meus_dados_admin(self, client, admin):
        login(client, 'admin_user')
        ok(client.get('/conta/meus-dados'))

    def test_consentimento_ja_aceito_redireciona(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/consentimento', follow_redirects=False)
        # fixture já tem consent → redireciona imediatamente
        assert r.status_code == 302

    def test_privacidade_autenticado(self, client, employee):
        login(client, 'emp_user')
        ok(client.get('/privacidade'))


# ── Relatórios ────────────────────────────────────────────────────────────────

class TestSmokeRelatorios:
    def test_relatorios_admin(self, client, admin, employee, vehicle):
        login(client, 'admin_user')
        ok(client.get('/relatorios/'))

    def test_relatorios_coordenador(self, client, coordinator, employee, vehicle):
        login(client, 'coord_user')
        ok(client.get('/relatorios/'))

    def test_exportar_excel(self, client, admin, employee, vehicle):
        login(client, 'admin_user')
        ok(client.get('/relatorios/exportar/excel'))

    def test_exportar_pdf(self, client, admin, employee, vehicle):
        login(client, 'admin_user')
        ok(client.get('/relatorios/exportar/pdf'))
