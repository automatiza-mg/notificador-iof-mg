# `.env.example` (documentado) — Notificador IOF MG

Este arquivo serve como **guia completo** para configurar variáveis de ambiente do **Notificador IOF MG**.

> ✅ **Como usar**
>
> 1. Copie o bloco **“Arquivo `.env.example` (copiar e colar)”** para um arquivo chamado `.env` na raiz do projeto.
> 2. Ajuste os valores conforme seu ambiente (local, Docker, Azure).
> 3. Suba a aplicação e valide usando o **Backtest** (em `APP_ENV=development`) ou chamando o endpoint **`/api/tasks/process-daily`** com `API_KEY`.

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
# EMAIL (SMTP) — FLASK-MAIL
# --------------------------------------------------------------
# Endereço do remetente (From)
MAIL_FROM_ADDRESS=seu-email@exemplo.com

# Host/porta do servidor SMTP
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587

# TLS/SSL
# Gmail na porta 587 => TLS true, SSL false
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Credenciais SMTP
MAIL_SMTP_USER=seu-email@gmail.com
MAIL_SMTP_PASSWORD=sua-senha-de-app


# --------------------------------------------------------------
# REDIS / RQ (OPCIONAL) — PROCESSAMENTO ASSÍNCRONO
# --------------------------------------------------------------
REDIS_URL=redis://localhost:6379/0


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

### 2.3 Banco de dados das **configurações** (SQLAlchemy/Alembic)
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

### 2.4 Banco de **busca** (SQLite FTS5) — `diarios.db`
- **`DIARIOS_DIR`** aponta para a pasta onde o app mantém o índice de busca.
- Dentro dela fica o arquivo:
  - `diarios.db` (com tabelas FTS5 e triggers)

**Local**: `DIARIOS_DIR=diarios`

**Azure**: `DIARIOS_DIR=/home/diarios` (persistente)

---

### 2.5 SMTP / Email
O app usa **Flask-Mail** e as variáveis abaixo:

- `MAIL_FROM_ADDRESS`
- `MAIL_SMTP_HOST`
- `MAIL_SMTP_PORT`
- `MAIL_USE_TLS`
- `MAIL_USE_SSL`
- `MAIL_SMTP_USER`
- `MAIL_SMTP_PASSWORD`

#### Gmail (recomendado)
- Use **Senha de App** (App Password), não a senha normal.
- Config típica:

```env
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_SMTP_USER=seu-email@gmail.com
MAIL_SMTP_PASSWORD=senha-de-app
```

#### MailHog (somente desenvolvimento)
Ideal para testar emails sem enviar de verdade.

```env
MAIL_SMTP_HOST=localhost
MAIL_SMTP_PORT=1025
MAIL_USE_TLS=false
MAIL_USE_SSL=false
MAIL_SMTP_USER=
MAIL_SMTP_PASSWORD=
MAIL_FROM_ADDRESS=noreply@local
```

#### SendGrid (exemplo)

```env
MAIL_SMTP_HOST=smtp.sendgrid.net
MAIL_SMTP_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_SMTP_USER=apikey
MAIL_SMTP_PASSWORD=SEU_TOKEN_SENDGRID
MAIL_FROM_ADDRESS=seu-email@dominio.com
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

