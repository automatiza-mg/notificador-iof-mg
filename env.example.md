# `.env.example` (documentado) — Notificador IOF MG

Este arquivo serve como **guia completo** para configurar variáveis de ambiente do **Notificador IOF MG**.

> ✅ **Como usar**
>
> 1. Copie o bloco **“Arquivo `.env.example` (copiar e colar)”** para um arquivo chamado `.env` na raiz do projeto.
> 2. Ajuste os valores conforme seu ambiente (local, Docker, Azure).
> 3. Suba a aplicação e valide usando o **Backtest** (em `APP_ENV=development`) ou chamando o endpoint **`/api/tasks/process-daily`** com `API_KEY`.

---

## ⚠️ ATENÇÃO DEVOPS / CLOUD ENGINEER (DEPLOY AZURE)

Se você está configurando este projeto em um **Azure App Service (Web App for Containers)**, é crucial entender a persistência do container:

1. A imagem Docker cria o banco de índices e de usuários em disco.
2. Se você não configurar as variáveis de diretório para a partição `/home` do Azure, **todos os alertas dos usuários e PDFs serão apagados** a cada deploy ou reboot da máquina.
3. Você **DEVE** definir no painel da Azure (Environment Variables):
   - `WEBSITES_ENABLE_APP_SERVICE_STORAGE=true`
   - `DIARIOS_DIR=/home/diarios`
   - `DATABASE_URL=sqlite:////home/instance/local.db`

Com essas 3 marcações, o `entrypoint.sh` criará as pastas automaticamente no disco persistente da Azure antes de ligar o servidor Gunicorn.

---

## 1) Arquivo `.env.example` (copiar e colar)

> ⚠️ **Nunca commite** seu `.env` com segredos reais. Mantenha apenas este exemplo no repositório.

```env
# ==============================================================
# NOTIFICADOR IOF MG — .env (EXEMPLO)
# ==============================================================

# --------------------------------------------------------------
# AMBIENTE
# --------------------------------------------------------------
# development | production | testing
APP_ENV=development

# Chave secreta do Flask (cookies/sessão/flash). Em produção, use um valor forte.
SECRET_KEY=troque-esta-chave-em-producao

# Nome (apenas informativo/logs)
APP_NAME=notificador-iof-mg

# (opcional) URL do client/front (se você tiver um front separado)
CLIENT_URL=http://localhost:5173


# --------------------------------------------------------------
# SEGURANÇA — ENDPOINT ADMIN
# --------------------------------------------------------------
# Protege o endpoint: POST /api/tasks/process-daily
# Gere um token longo/aleatório (>= 32 chars). Ex.: openssl rand -hex 32
API_KEY=coloque-um-token-longo-aqui


# --------------------------------------------------------------
# BANCO DE DADOS (CONFIGURAÇÕES DO APP — SQLALCHEMY/ALEMBIC)
# --------------------------------------------------------------
# Por padrão, o projeto usa SQLite.
# Local (recomendado):
DATABASE_URL=sqlite:///instance/local.db

# Produção no Azure App Service (com storage persistente /home):
# DATABASE_URL=sqlite:////home/instance/local.db

# PostgreSQL (opcional):
# DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME


# --------------------------------------------------------------
# DIRETÓRIO DO BANCO DE BUSCA (FTS5) — diarios.db
# --------------------------------------------------------------
# Aqui fica o banco de índice do Diário Oficial (SQLite FTS5).
# Local:
DIARIOS_DIR=diarios

# Azure (persistência em /home):
# DIARIOS_DIR=/home/diarios


# --------------------------------------------------------------
# EMAIL — AZURE EM PRODUÇÃO / SMTP EM DESENVOLVIMENTO
# --------------------------------------------------------------
# Provider de envio: azure (produção) | smtp (desenvolvimento)
MAIL_PROVIDER=azure

# Azure Communication Services Email (produção)
AZURE_EMAIL_ENDPOINT=https://automatiza-comms.brazil.communication.azure.com/
AZURE_EMAIL_SENDER_ADDRESS=DoNotReply@SEU-DOMINIO.azurecomm.net
AZURE_COMMUNICATION_CONNECTION_STRING=endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=troque-esta-chave

# SMTP (desenvolvimento local / fallback)
# Endereço do remetente (From)
MAIL_FROM_ADDRESS=seu-email@exemplo.com

# Host/porta do servidor SMTP
MAIL_SMTP_HOST=localhost
MAIL_SMTP_PORT=1025

# TLS/SSL
MAIL_USE_TLS=false
MAIL_USE_SSL=false

# Credenciais SMTP
MAIL_SMTP_USER=
MAIL_SMTP_PASSWORD=


# --------------------------------------------------------------
# REDIS / RQ (OPCIONAL) — PROCESSAMENTO ASSÍNCRONO
# --------------------------------------------------------------
REDIS_URL=redis://localhost:6379/0


# --------------------------------------------------------------
# MICROSOFT ENTRA ID (SSO)
# --------------------------------------------------------------
# Login via Microsoft (OIDC). Não commite ENTRA_CLIENT_SECRET; em produção
# use App Settings do Azure ou Key Vault.
ENTRA_TENANT_ID=seu-tenant-id
ENTRA_CLIENT_ID=seu-client-id
ENTRA_CLIENT_SECRET=nao-commitar-em-producao-use-app-settings
# Authority (ou deixe vazio para derivar de ENTRA_TENANT_ID)
ENTRA_AUTHORITY=https://login.microsoftonline.com/SEU_TENANT_ID
# Redirect URI exata registrada no app Entra (ex.: DEV)
ENTRA_REDIRECT_URI=http://localhost:5000/auth/callback
# Escopos (MVP: apenas login)
ENTRA_SCOPES=openid profile email


# --------------------------------------------------------------
# GUNICORN (PRODUÇÃO / DOCKER)
# --------------------------------------------------------------
# Porta que o App Service/Docker expõe para o Gunicorn
PORT=8000

# Timeout (em segundos). PDFs podem demorar.
GUNICORN_TIMEOUT=300

# Número de workers (default: (2 * cpu) + 1, limitado a 4 no config)
GUNICORN_WORKERS=2

# Nível de log do Gunicorn
LOG_LEVEL=info


# --------------------------------------------------------------
# IOF (OPCIONAL) — credenciais (não usadas por padrão no código atual)
# --------------------------------------------------------------
IOF_USERNAME=
IOF_PASSWORD=
```

---

## 2) Explicação por blocos (o que cada variável faz)

### 2.1 Ambiente
- **`APP_ENV`**: define comportamento geral (ex.: `development` habilita Backtest; `production` desabilita Backtest por padrão).
- **`SECRET_KEY`**: usado pelo Flask para sessão/flash messages. Em produção deve ser **forte** e **secreta**.
- **`APP_NAME`**: identificador textual.
- **`CLIENT_URL`**: útil se existir front separado (não é obrigatório).

---

### 2.2 Segurança do endpoint administrativo
- **`API_KEY`**: protege o endpoint administrativo:
  - `POST /api/tasks/process-daily?api_key=<API_KEY>`

> 🔐 Recomendações:
> - Gere com `openssl rand -hex 32`
> - Não compartilhe em logs, prints ou commits.

---

### 2.3 Entra ID (SSO)
Login com **Microsoft Entra ID** (Azure AD) via OIDC. Variáveis:

- **`ENTRA_TENANT_ID`**: ID do tenant (diretório) no Azure.
- **`ENTRA_CLIENT_ID`**: ID do aplicativo registrado em Entra.
- **`ENTRA_CLIENT_SECRET`**: segredo do app. **Nunca commite**; em produção use App Settings ou Key Vault.
- **`ENTRA_AUTHORITY`**: URL da autoridade (ex.: `https://login.microsoftonline.com/<TENANT_ID>`). Se omitida, é derivada de `ENTRA_TENANT_ID`.
- **`ENTRA_REDIRECT_URI`**: URI de redirecionamento **exata** registrada no app (ex.: `http://localhost:5000/auth/callback` para DEV).
- **`ENTRA_SCOPES`**: escopos OIDC (MVP: `openid profile email`).

No portal Azure (Entra): registre um aplicativo, defina a redirect URI e use o client secret apenas em ambiente seguro. Para o botão **Sair** encerrar também a sessão da Microsoft ("Stay signed in"), adicione a URL da página de login (ex.: `http://localhost:5000/login` e em produção `https://seu-dominio/login`) em **Redirect URIs** do app; ela é usada como `post_logout_redirect_uri` ao redirecionar para o logout da Microsoft.

---

### 2.4 Banco de dados das **configurações** (SQLAlchemy/Alembic)
- **`DATABASE_URL`**: conexão do SQLAlchemy, onde ficam as tabelas:
  - `search_configs` (configurações)
  - `search_terms` (termos)

**SQLite (local)**
- Bom para desenvolvimento e ambientes simples.
- Exemplo: `sqlite:///instance/local.db`

**SQLite (Azure App Service)**
- Use `/home` com storage habilitado:
- Exemplo: `sqlite:////home/instance/local.db`

**PostgreSQL (opcional)**
- Recomendado para produção mais robusta (conexões concorrentes, backup, etc.).
- Exemplo:
  - `postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME`

> ✅ Dica: migrations rodam via `alembic upgrade head` no startup do container (ver `entrypoint.sh`).

---

### 2.5 Banco de **busca** (SQLite FTS5) — `diarios.db`
- **`DIARIOS_DIR`** aponta para a pasta onde o app mantém o índice de busca.
- Dentro dela fica o arquivo:
  - `diarios.db` (com tabelas FTS5 e triggers)

**Local**: `DIARIOS_DIR=diarios`

**Azure**: `DIARIOS_DIR=/home/diarios` (persistente)

---

### 2.6 Email
O app suporta dois providers:

- **Azure Communication Services Email** em produção
- **SMTP/Flask-Mail** em desenvolvimento local

#### Provider selecionado
- **`MAIL_PROVIDER`**: define o provider de email (`azure` ou `smtp`).
- Se não for definido explicitamente, o app usa `azure` em `production` e `smtp` nos demais ambientes.

#### Azure Communication Services Email (produção)
- **`AZURE_EMAIL_ENDPOINT`**: endpoint do recurso ACS.
- **`AZURE_EMAIL_SENDER_ADDRESS`**: remetente autorizado no domínio do ACS.
- **`AZURE_COMMUNICATION_CONNECTION_STRING`**: connection string do recurso de comunicação.

Exemplo:

```env
MAIL_PROVIDER=azure
AZURE_EMAIL_ENDPOINT=https://automatiza-comms.brazil.communication.azure.com/
AZURE_EMAIL_SENDER_ADDRESS=DoNotReply@291ec9eb-c86f-49d0-9a0c-ff2e079089f7.azurecomm.net
AZURE_COMMUNICATION_CONNECTION_STRING=endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=SEU_ACCESS_KEY
```

> 🔐 Recomendação: use App Settings ou Key Vault para armazenar a connection string. Se a chave tiver sido exposta em prints ou chats, faça rotação imediatamente.

#### SMTP / Flask-Mail (desenvolvimento)
Variáveis usadas quando `MAIL_PROVIDER=smtp`:

- `MAIL_FROM_ADDRESS`
- `MAIL_SMTP_HOST`
- `MAIL_SMTP_PORT`
- `MAIL_USE_TLS`
- `MAIL_USE_SSL`
- `MAIL_SMTP_USER`
- `MAIL_SMTP_PASSWORD`

#### MailHog (somente desenvolvimento)
Ideal para testar emails sem enviar de verdade.

```env
MAIL_PROVIDER=smtp
MAIL_SMTP_HOST=localhost
MAIL_SMTP_PORT=1025
MAIL_USE_TLS=false
MAIL_USE_SSL=false
MAIL_SMTP_USER=
MAIL_SMTP_PASSWORD=
MAIL_FROM_ADDRESS=noreply@local
```

#### Gmail (desenvolvimento ou contingência local)
- Use **Senha de App** (App Password), não a senha normal.

```env
MAIL_PROVIDER=smtp
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_SMTP_USER=seu-email@gmail.com
MAIL_SMTP_PASSWORD=senha-de-app
MAIL_FROM_ADDRESS=seu-email@gmail.com
```

---

### 2.6 Redis / RQ (opcional)
- **`REDIS_URL`**: habilita enfileiramento de jobs via **RQ**.

Exemplo local:

```env
REDIS_URL=redis://localhost:6379/0
```

> Observação: o endpoint `/api/tasks/process-daily` tem implementação **síncrona** (sem Redis) para rodar mesmo sem worker.

---

### 2.7 Gunicorn (produção)
- `PORT`: porta do serviço.
- `GUNICORN_TIMEOUT`: essencial porque extração de PDF pode levar tempo.
- `GUNICORN_WORKERS`: número de workers.
- `LOG_LEVEL`: nível de log.

---

## 3) Exemplos de execução rápida

### 3.1 Rodar local (sem Docker)

```bash
# 1) Instale dependências
uv sync

# 2) Migrations
uv run alembic upgrade head

# 3) Start
uv run flask run
```

### 3.2 Testar o processamento diário (com API_KEY)

```bash
curl -X POST "http://localhost:5000/api/tasks/process-daily?api_key=$API_KEY"

curl -X POST \
  "http://localhost:5000/api/tasks/process-daily?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-01-14"}'
```

---

## 4) Guia de configuração para Azure App Service (container)

### Variáveis recomendadas

```env
APP_ENV=production
DIARIOS_DIR=/home/diarios
DATABASE_URL=sqlite:////home/instance/local.db
PORT=8000
```

E habilite:
- `WEBSITES_ENABLE_APP_SERVICE_STORAGE=true`

> O `entrypoint.sh` cria os diretórios persistentes e roda migrations automaticamente.

---

## 5) Checklist de validação

- [ ] `API_KEY` definida e usada no endpoint `/api/tasks/process-daily`
- [ ] `MAIL_*` configurado e testado (Backtest em DEV ajuda)
- [ ] `poppler-utils` instalado (ou usar Docker)
- [ ] `DATABASE_URL` aponta para local persistente correto
- [ ] `DIARIOS_DIR` aponta para pasta correta (principalmente no Azure)

---

## 6) Dicas de segurança (fortemente recomendadas)

- ✅ Nunca commitar `.env` com segredos.
- ✅ Em produção, rotacione `API_KEY` e `SECRET_KEY`.
- ✅ Se usar Postgres, use SSL/Network restrictions e segredo via Key Vault/App Settings.
