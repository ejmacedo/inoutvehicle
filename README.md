# InOut Veículos

Sistema web de controle de entrada e saída de veículos da empresa.  
Desenvolvido com **Flask** + **SQLite**, rodando localmente via ambiente virtual Python.

---

## Pré-requisitos

- [Python 3.10+](https://www.python.org/downloads/) instalado e adicionado ao PATH
- Acesso ao prompt de comando (CMD) ou PowerShell

---

## Primeiros passos (instalação inicial)

Execute estes passos **apenas na primeira vez** que configurar o projeto na máquina.

### 1. Baixe o projeto do GitHub

Acesse o repositório, clique em **Code → Download ZIP**, extraia e mova a pasta para:

```
C:\Users\Eduardo\Documents\inoutvehicle\
```

A estrutura ficará assim:

```
C:\Users\Eduardo\Documents\inoutvehicle\
└── inoutvehicle-main\
    ├── app\
    ├── run.py
    ├── seed.py
    ├── requirements.txt
    └── ...
```

### 2. Crie o ambiente virtual

Abra o prompt de comando e navegue até a pasta do projeto:

```cmd
cd C:\Users\Eduardo\Documents\inoutvehicle
```

Crie o ambiente virtual (feito apenas uma vez):

```cmd
python -m venv .venv
```

### 3. Ative o ambiente virtual

```cmd
.\.venv\Scripts\activate
```

O prompt passará a exibir `(.venv)` no início, indicando que o ambiente está ativo.

### 4. Acesse a pasta principal do projeto

```cmd
cd inoutvehicle-main
```

### 5. Instale as dependências

```cmd
pip install -r requirements.txt
```

### 6. Inicialize o banco de dados

```cmd
python seed.py
```

Este comando cria o banco de dados e o usuário administrador padrão:

| Campo    | Valor  |
|----------|--------|
| Usuário  | `root` |
| Senha    | `1234` |

### 7. Inicie o servidor

```cmd
python run.py
```

Acesse no navegador: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Uso diário (como iniciar o projeto)

Sempre que quiser usar o sistema, abra o prompt de comando e execute:

```cmd
cd C:\Users\Eduardo\Documents\inoutvehicle
.\.venv\Scripts\activate
cd inoutvehicle-main
python run.py
```

Para encerrar o servidor, pressione `Ctrl + C` no prompt.

---

## Aplicando atualizações do GitHub

Quando houver uma nova versão disponível no repositório, siga estes passos:

### 1. Baixe a versão atualizada

No GitHub, clique em **Code → Download ZIP**, extraia e **substitua** a pasta `inoutvehicle-main` pela nova versão.

### 2. Ative o ambiente virtual (se ainda não estiver ativo)

```cmd
cd C:\Users\Eduardo\Documents\inoutvehicle
.\.venv\Scripts\activate
cd inoutvehicle-main
```

### 3. Atualize as dependências

```cmd
pip install -r requirements.txt
```

> Execute este passo sempre que uma atualização adicionar novas bibliotecas.

### 4. Atualize o banco de dados

```cmd
python seed.py
```

> ⚠ **Atenção:** se a atualização incluir mudanças no banco de dados (novas colunas ou tabelas), pode ser necessário rodar com a flag `--reset`, que **apaga todos os dados**:
> ```cmd
> python seed.py --reset
> ```
> O histórico de atualizações abaixo informa quando isso é necessário.

### 5. Inicie o servidor

```cmd
python run.py
```

---

## Configuração de e-mail (opcional)

Para habilitar as notificações por e-mail e a recuperação de senha, crie um arquivo `.env` na pasta `inoutvehicle-main` com o seguinte conteúdo:

```env
SECRET_KEY=uma-chave-secreta-longa-e-aleatoria
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
MAIL_DEFAULT_SENDER=InOut Veículos <seu-email@gmail.com>
```

> **Gmail:** é necessário criar uma "Senha de App" em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requer verificação em duas etapas ativada).  
> Sem o `.env`, o sistema funciona normalmente — apenas sem envio de e-mails.

---

## Perfis de acesso

| Perfil        | O que pode fazer |
|---------------|------------------|
| **Admin**     | Gerenciar usuários, veículos e visualizar relatórios completos |
| **Coordenador** | Aprovar ou recusar solicitações dos seus funcionários; gerar relatórios |
| **Funcionário** | Solicitar uso de veículo e acompanhar suas solicitações |
| **Portaria**  | Registrar saída (com odômetro) e retorno dos veículos |

---

## Histórico de versões

| Versão | Resumo | Precisa de `--reset`? |
|--------|--------|-----------------------|
| **v0.1** | Versão inicial: login, solicitação, aprovação, portaria, admin | ✅ Sim (instalação nova) |
| **v0.2** | Múltiplos coordenadores, saída/retorno real, e-mail, relatórios Excel/PDF | ✅ Sim |
| **v0.3** | Toasts, recuperação de senha, validações pt-BR, odômetro na saída | ✅ Sim |
