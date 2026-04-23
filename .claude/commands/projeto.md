# InOut Veículos — Contexto completo do projeto

Ao receber este comando, carregue todo o contexto abaixo como conhecimento ativo da sessão antes de responder qualquer coisa.

---

## Visão geral

**InOut Veículos** é um sistema web de controle de entrada e saída de veículos corporativos.
Stack: **Python 3.11 · Flask · SQLite · SQLAlchemy · Flask-Login · Flask-WTF · Bootstrap 5.3**.
Repositório: `ejmacedo/inoutvehicle`. Branch de desenvolvimento: `claude/vehicle-request-app-p1eRO`.

---

## Estrutura de pastas

```
inoutvehicle/
├── app/
│   ├── __init__.py          # factory, session timeout, security headers
│   ├── models.py            # User, Vehicle, VehicleRequest, DriverReservation, AuditLog
│   ├── extensions.py        # db, login_manager, migrate, csrf
│   ├── decorators.py        # @role_required
│   ├── validators.py        # strong_password (wtforms)
│   ├── audit.py             # log_action()
│   ├── security_utils.py    # brute-force protection (in-memory)
│   ├── email_utils.py       # notificações por e-mail
│   ├── utils.py             # get_unavailable_vehicle_ids()
│   ├── auth/                # login, logout, reset de senha
│   ├── employee/            # funcionário: criar/ver solicitações
│   ├── coordinator/         # aprovar/recusar, motoristas, reservas
│   ├── security/            # portaria: registrar saída/retorno
│   ├── admin/               # CRUD usuários, veículos, log de auditoria
│   ├── reports/             # relatórios com filtros
│   ├── profile/             # trocar senha
│   ├── main/                # index/roteamento inicial
│   └── templates/
│       ├── base.html        # layout com sidebar por perfil
│       ├── admin/
│       │   └── audit_log.html  # tabela paginada com filtros
│       └── ...
├── tests/
│   ├── conftest.py          # fixtures: app, client, usuários, veículos, solicitações
│   ├── test_auth.py
│   ├── test_admin.py
│   ├── test_employee.py
│   ├── test_coordinator.py
│   ├── test_security.py
│   ├── test_profile.py
│   └── test_reports.py
├── backup.py                # backup automático do SQLite (mantém 30 arquivos)
├── seed.py                  # cria tabelas + usuários/veículos de teste fixos
├── run.py                   # ponto de entrada (flask run)
├── config.py                # configurações de sessão, cookie, e-mail
├── requirements.txt
├── instalar.bat             # Windows: cria .venv na pasta pai, instala deps
├── iniciar.bat              # Windows: ativa .venv da pasta pai, sobe servidor
└── atualizar.bat            # Windows: git pull → backup → seed → run
```

---

## Perfis de usuário (Role)

| Perfil | Constante | Acesso |
|---|---|---|
| Administrador | `Role.ADMIN` | tudo: CRUD usuários/veículos, log de auditoria, relatórios |
| Coordenador | `Role.COORDINATOR` | aprovar/recusar solicitações dos seus funcionários, criar motoristas e reservas |
| Funcionário | `Role.EMPLOYEE` | criar/ver suas próprias solicitações de veículo |
| Portaria | `Role.SECURITY` | registrar saída e retorno de veículos |
| Motorista | `Role.DRIVER` | ver suas reservas (criadas pelo coordenador) |

---

## Modelos principais (app/models.py)

### User
Campos: `id, username, email, full_name, password_hash, role, is_active, created_at`
Relacionamentos: `coordinators` (M2M via `employee_coordinators`), `requests`, `audit_logs`

### Vehicle
Campos: `id, name, plate, model, is_active`

### VehicleRequest
Campos: `id, employee_id, vehicle_id, departure_datetime, expected_return_datetime, actual_departure_datetime, actual_return_datetime, odometer_departure, odometer_return, reason, returns_to_company, status, coordinator_notes, portaria_obs, created_at, updated_at`
Status: `pending | approved | rejected`

### DriverReservation
Criada diretamente pelo coordenador para motoristas — auto-aprovada.
Campos: `id, coordinator_id, driver_id, vehicle_id, departure_datetime, expected_return_datetime, actual_departure_datetime, actual_return_datetime, odometer_departure, odometer_return, reason, portaria_obs, created_at`

### AuditLog
Campos: `id, user_id, username, action, description, ip_address, created_at`

---

## Camadas de segurança implementadas (v0.5)

### 1. Log de Auditoria (`app/audit.py`)
```python
from app.audit import log_action
log_action('ACAO', 'descrição opcional')
```
- Nunca quebra o fluxo principal (try/except)
- Visualização em `/admin/auditoria` com filtro por ação/usuário e paginação
- Ações registradas: `LOGIN_OK, LOGIN_FAIL, LOGIN_BLOQUEADO, LOGOUT, SENHA_REDEFINIDA, SENHA_ALTERADA, SOLICITACAO_CRIADA, SOLICITACAO_APROVADA, SOLICITACAO_RECUSADA, MOTORISTA_CRIADO, MOTORISTA_ATUALIZADO, FUNCIONARIO_ATUALIZADO, RESERVA_MOTORISTA_CRIADA, SAIDA_REGISTRADA, RETORNO_REGISTRADO, SAIDA_MOTORISTA, RETORNO_MOTORISTA, USUARIO_CRIADO, USUARIO_ATUALIZADO, VEICULO_CRIADO, VEICULO_ATUALIZADO`

### 2. Proteção Brute-Force (`app/security_utils.py`)
```python
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
# funções: is_blocked(ip), record_failure(ip), clear(ip), remaining_lockout_minutes(ip)
```
- Dict em memória por IP (reseta ao reiniciar o servidor — comportamento aceitável para uso local)
- Integrado em `app/auth/routes.py` no endpoint de login

### 3. Session Timeout (`app/__init__.py`)
```python
@app.before_request
def check_session_timeout():
    # verifica session['_last_active'], expira em 30 min de inatividade
```

### 4. Senha Forte (`app/validators.py`)
```python
def strong_password(form, field):
    # mínimo 8 chars + 1 maiúscula + 1 minúscula + 1 número
```
- Aplicado em: `admin/forms.py`, `auth/forms.py`, `coordinator/forms.py`, `profile/forms.py`
- Compatible com `Optional()`: não valida se campo vazio (para edição sem trocar senha)

### 5. Headers HTTP de Segurança (`app/__init__.py`)
```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
```

### 6. Backup Automático (`backup.py`)
- Copia `inoutvehicle.db` para `backups/inoutvehicle_YYYYMMDD_HHMMSS.db`
- Mantém os 30 backups mais recentes
- Executado automaticamente no `atualizar.bat` (passo 3/5)

### 7. Proteção SQL Injection
- Toda interação com DB via SQLAlchemy ORM (zero SQL raw)

### 8. Proteção CSRF
- Flask-WTF com `csrf.init_app(app)` em todos os formulários

### 9. Hashing de Senhas
- Werkzeug `generate_password_hash / check_password_hash`

### 10. Cookie de Sessão
```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
```

---

## Testes (`tests/`)

**107 testes** cobrindo todos os fluxos.

### Configuração chave (`tests/conftest.py`)
```python
class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool,   # essencial: todos os contextos compartilham a mesma conexão
    }
    WTF_CSRF_ENABLED = False
```

### Senha padrão nos testes
- Usuários criados por fixture: `'Senha123'` (tem maiúscula + minúscula + número)
- Helper `login(client, username)` usa `'Senha123'` como padrão
- Quando POST em formulário com senha nova usar: `'NovaSenha456'` ou similar (não `'senha123'`)

### Fixtures principais
`admin, coordinator, coordinator2, employee, employee2, driver, security_user, inactive_user, vehicle, vehicle2, pending_request, approved_request, departed_request, driver_reservation`

### Rodar os testes
```bash
pytest tests/ -q
pytest tests/test_auth.py -v   # arquivo específico
```

---

## Dados de teste fixos (`seed.py`)

Senha padrão de todos: **`Senha1234`**

| Perfil | Login |
|---|---|
| Admin | `root` |
| Coordenador | `carlos.lima` |
| Coordenador | `fernanda.souza` |
| Funcionário | `eduardo.macedo` |
| Funcionário | `matheus.henrique` |
| Motorista | `joao.silva` |
| Motorista | `pedro.alves` |
| Motorista | `lucas.pereira` |
| Portaria | `portaria` |

Veículos: Gol Prata (ABC-1234), Uno Branco (DEF-5678), HB20 Preto (GHI-9012), Strada Prata (JKL-3456), S10 Branca (MNO-7890)

```bash
python seed.py           # cria tabelas e dados sem apagar existentes
python seed.py --reset   # DROP ALL e recria do zero
```

---

## Scripts Windows

```
instalar.bat   → cria .venv em ../  → pip install -r requirements.txt → seed.py
iniciar.bat    → ativa .venv de ../  → cd inoutvehicle → python run.py
atualizar.bat  → git pull origin main → pip install → backup.py → seed.py → run.py
```

Todos usam `cd /d "%~dp0.."` para garantir que o `.venv` seja encontrado na pasta pai.

---

## Rotas principais por blueprint

| Blueprint | Prefixo | Rotas-chave |
|---|---|---|
| `auth` | `/` | `/login`, `/logout`, `/recuperar-senha` |
| `employee` | `/funcionario` | `/dashboard`, `/nova-solicitacao` |
| `coordinator` | `/coordenador` | `/dashboard`, `/solicitacao/<id>/aprovar`, `/motoristas/novo`, `/reservas-motorista/nova` |
| `security` | `/portaria` | `/dashboard`, `/saida/<id>`, `/retorno/<id>` |
| `admin` | `/admin` | `/usuarios`, `/veiculos`, `/auditoria` |
| `reports` | `/relatorios` | `/` (filtros por status/data/usuário) |
| `profile` | `/conta` | `/trocar-senha` |

---

## Problemas conhecidos e soluções aplicadas

### SQLite in-memory em testes
Cada `app_context()` cria uma conexão nova → DB separado → fixtures somem.
**Solução:** `StaticPool` no `TestConfig` força uma única conexão compartilhada.

### Conflito de merge ao PR
A feature branch divergiu do `main`. Fluxo correto:
```bash
git fetch origin main
git merge origin/main --no-edit
# resolver conflitos com: git checkout --ours <arquivo>
git add .
git commit
git push -u origin claude/vehicle-request-app-p1eRO
```

### atualizar.bat com path errado
O `.venv` fica na pasta **pai** do repositório. Sempre usar `cd /d "%~dp0.."` antes de ativar.

---

## Como continuar o desenvolvimento

1. Criar nova feature: branch `claude/nome-da-feature`
2. Adicionar `log_action('ACAO', 'descrição')` em toda ação relevante nas rotas
3. Novos formulários com senha: incluir `strong_password` do `app/validators.py`
4. Novos testes: usar as fixtures de `conftest.py`; senha padrão `'Senha123'`; formulários com senha nova usam senhas com maiúscula+número
5. Push: `git push -u origin <branch>` → abrir PR para `main`
