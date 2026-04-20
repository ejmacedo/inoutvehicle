# InOut Veículos

Sistema web de controle de entrada e saída de veículos da empresa.  
Desenvolvido com **Flask** + **SQLite**, rodando localmente via ambiente virtual Python.

---

## Pré-requisitos

Instale os dois programas abaixo **antes de qualquer coisa**:

| Programa | Link | Observação |
|----------|------|------------|
| **Python 3.10+** | https://www.python.org/downloads/ | Marque **"Add Python to PATH"** durante a instalação |
| **Git** | https://git-scm.com/download/win | Deixe todas as opções padrão |

---

## Instalação inicial (feita apenas uma vez)

### 1. Clone o repositório

Abra o **Prompt de Comando** e execute:

```cmd
cd C:\Users\Eduardo\Documents
git clone https://github.com/ejmacedo/inoutvehicle.git
```

Isso criará a pasta `C:\Users\Eduardo\Documents\inoutvehicle\` já conectada ao GitHub.

### 2. Execute o instalador

Navegue até a pasta criada e dê **duplo clique** em `instalar.bat`.

O script irá automaticamente:
- Criar o ambiente virtual `.venv`
- Instalar todas as dependências
- Criar o banco de dados e o usuário administrador

Usuário criado:

| Campo   | Valor  |
|---------|--------|
| Usuário | `root` |
| Senha   | `1234` |

---

## Uso diário

Dê **duplo clique** em `iniciar.bat`.

O servidor será iniciado e estará disponível em: [http://127.0.0.1:5000](http://127.0.0.1:5000)

Para encerrar, pressione `Ctrl + C` na janela do prompt.

---

## Aplicar atualizações

Sempre que houver uma nova versão, dê **duplo clique** em `atualizar.bat`.

O script irá automaticamente:
1. Baixar as atualizações do GitHub (`git pull`)
2. Instalar novas dependências (se houver)
3. Atualizar o banco de dados
4. Iniciar o servidor

> ⚠ **Atenção:** algumas atualizações exigem reinicialização do banco de dados.  
> Quando isso acontecer, estará indicado no histórico de versões abaixo.  
> Para reinicializar o banco (**apaga todos os dados**), abra o prompt, ative o venv e rode:
> ```cmd
> cd C:\Users\Eduardo\Documents\inoutvehicle
> .\.venv\Scripts\activate
> cd inoutvehicle
> python seed.py --reset
> ```

---

## Configuração de e-mail (opcional)

Para habilitar notificações por e-mail e recuperação de senha, crie o arquivo `.env` dentro da pasta `inoutvehicle\` com o conteúdo:

```env
SECRET_KEY=uma-chave-secreta-longa-e-aleatoria
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
MAIL_DEFAULT_SENDER=InOut Veículos <seu-email@gmail.com>
```

> **Gmail:** crie uma "Senha de App" em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requer verificação em duas etapas).  
> Sem o `.env`, o sistema funciona normalmente — apenas sem envio de e-mails.

---

## Perfis de acesso

| Perfil          | O que pode fazer |
|-----------------|------------------|
| **Admin**       | Gerenciar usuários e veículos; relatórios completos |
| **Coordenador** | Aprovar/recusar solicitações dos seus funcionários; relatórios |
| **Funcionário** | Solicitar veículo e acompanhar suas solicitações |
| **Portaria**    | Registrar saída (com odômetro) e retorno dos veículos |

---

## Histórico de versões

| Versão | Resumo | Reinicializar banco? |
|--------|--------|----------------------|
| **v0.1** | Versão inicial: login, solicitação, aprovação, portaria, admin | ✅ Sim (instalação nova) |
| **v0.2** | Múltiplos coordenadores, saída/retorno real, e-mail, relatórios Excel/PDF | ✅ Sim |
| **v0.3** | Toasts, recuperação de senha, validações pt-BR, odômetro na saída | ✅ Sim |
| **v0.4** | Perfil motorista, reservas pelo coordenador, troca de veículo na aprovação, disponibilidade real, portaria unificada com filtros, KM no retorno, data+hora reais, OBS 30 min, trocar senha | ⚠️ `atualizar.bat` faz a migração automática — sem perda de dados |
