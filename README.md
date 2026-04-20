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

## Os três scripts disponíveis

| Script | Quando usar |
|--------|-------------|
| `instalar.bat` | **Apenas uma vez** — na primeira configuração do projeto na máquina |
| `atualizar.bat` | **Quando houver novidades** — sempre que uma nova versão for publicada no GitHub |
| `iniciar.bat` | **No dia a dia** — para simplesmente ligar o sistema normalmente |

---

## `instalar.bat` — Use apenas uma vez

> ⚠️ **Execute este script somente na primeira vez que configurar o projeto na sua máquina.**  
> Rodá-lo novamente em uma instalação já existente não causa problemas, mas é desnecessário.

**O que ele faz:**
1. Verifica se Python e Git estão instalados
2. Cria o ambiente virtual `.venv` dentro da pasta do projeto
3. Instala todas as bibliotecas necessárias (`requirements.txt`)
4. Cria o banco de dados e o usuário administrador padrão

**Usuário criado automaticamente:**

| Campo   | Valor  |
|---------|--------|
| Usuário | `root` |
| Senha   | `1234` |

---

## `iniciar.bat` — Use no dia a dia

> ✅ **Este é o script que você vai usar na grande maioria das vezes.**

**Use quando:**
- Quiser abrir o sistema para uso normal
- Não houver nenhuma atualização pendente no GitHub
- Reiniciar o servidor após ter fechado

**O que ele faz:**
1. Ativa o ambiente virtual
2. Inicia o servidor Flask

Após executar, acesse no navegador: [http://127.0.0.1:5000](http://127.0.0.1:5000)

Para encerrar o servidor, pressione `Ctrl + C` na janela do prompt.

---

## `atualizar.bat` — Use quando houver nova versão

> 🔄 **Use este script quando for avisado que uma nova versão foi publicada.**  
> Ele substitui o `iniciar.bat` nesse dia — você não precisa rodar os dois.

**Use quando:**
- For informado que há uma nova versão disponível
- Quiser garantir que está rodando a versão mais recente

**O que ele faz:**
1. Ativa o ambiente virtual
2. Baixa as atualizações do GitHub (`git pull`)
3. Instala novas bibliotecas, se houver
4. Atualiza o banco de dados
5. Inicia o servidor automaticamente

> ⚠️ **Atenção com o banco de dados:** algumas atualizações exigem reinicialização
> completa do banco, o que **apaga todos os dados cadastrados**.  
> Isso sempre será informado no histórico de versões abaixo antes de você atualizar.  
> Quando necessário, abra o prompt, entre na pasta do projeto e rode manualmente:
> ```cmd
> cd C:\Users\Eduardo\Documents\inoutvehicle
> .\.venv\Scripts\activate
> python seed.py --reset
> ```

---

## Instalação inicial (passo a passo completo)

Siga estes passos **apenas na primeira vez**:

### 1. Clone o repositório

Abra o **Prompt de Comando** e execute:

```cmd
cd C:\Users\Eduardo\Documents
git clone https://github.com/ejmacedo/inoutvehicle.git
```

Isso criará a pasta `inoutvehicle\` já conectada ao GitHub.

### 2. Execute o instalador

Abra a pasta `inoutvehicle\` no Explorer e dê **duplo clique em `instalar.bat`**.

Aguarde a conclusão. Ao final aparecerá a mensagem:
```
Instalacao concluida com sucesso!
Para iniciar o sistema, execute: iniciar.bat
```

### 3. Inicie o sistema

Dê **duplo clique em `iniciar.bat`** e acesse [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## Configuração de e-mail (opcional)

Para habilitar notificações por e-mail e recuperação de senha, crie um arquivo chamado `.env`
dentro da pasta `inoutvehicle\` com o seguinte conteúdo:

```env
SECRET_KEY=uma-chave-secreta-longa-e-aleatoria
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
MAIL_DEFAULT_SENDER=InOut Veículos <seu-email@gmail.com>
```

> **Gmail:** crie uma "Senha de App" em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
> (requer verificação em duas etapas ativada).  
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
