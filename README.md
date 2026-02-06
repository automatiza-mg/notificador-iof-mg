# Notificador IOF MG

> Sistema de notificações do **Diário Oficial de Minas Gerais (Jornal Minas Gerais)**: você cadastra termos de interesse e recebe **alertas por e-mail** quando esses termos aparecem no Diário Oficial.

## ✨ Principais funcionalidades

- 🔎 **Busca por termos (até 5 por configuração)**
  - Busca **exata** (termo completo) ou **parcial** (substring)
- 📬 **Notificações por e-mail (até 5 destinatários)**
  - Assunto configurável por configuração
- 📎 **Anexo CSV opcional** com todos os resultados encontrados (compatível com Excel)
- 🌐 **Interface Web** para CRUD de configurações (criar/editar/ativar/desativar/deletar)
- 🧪 **Backtest (DEV)**: testar configurações em datas específicas antes de ativar
- ⚡ **Motor de busca Full-Text (SQLite FTS5)** para performance na busca
- 🧩 **API REST** para integração / automação
- 🐳 **Docker** pronto para produção (Gunicorn + migrations no startup)
- ☁️ **Deploy automatizado no Azure App Service** via GitHub Actions (OIDC) + ACR

---

## 🧭 Visão rápida (5 minutos)

1) **Instalar dependências** (Python + Poppler)

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y poppler-utils
```

2) **Configurar ambiente**

```bash
# (recomendado) use uv para instalar dependências
uv sync

# crie um arquivo .env (veja template abaixo)
cp -n .env.example .env 2>/dev/null || true
```

3) **Rodar migrations**

```bash
uv run alembic upgrade head
```

4) **Subir a aplicação (Web UI + API)**

```bash
uv run flask run
# ou: uv run python run.py
```

5) **Acessar**

- Web UI: http://localhost:5000
- API: http://localhost:5000/api

---

## 🗺️ Mapa do fluxo (alto nível)

```text
      (Agendador externo)                     (Aplicação)
   Cron/Logic App/Job -> POST /api/tasks/process-daily  
                         |  (consulta API v1 do jornal)
                         v
                 Baixa PDF (Base64) -> Extrai texto (poppler)
                         |
                         v
                   Indexa no SQLite FTS5 (diarios.db)
                         |
                         v
                Para cada SearchConfig ativa:
                 - Busca termos (exato/parcial)
                 - Gera highlights + links
                 - Envia e-mail (CSV opcional)
```

> **Agendamento:** a aplicação expõe um endpoint protegido por `API_KEY` para disparar o processamento diário. Você pode agendar via Azure Logic Apps, Cron, GitHub Actions, etc.

---

## 🧱 Arquitetura do projeto

### Componentes principais

- **Flask** (Web UI + API)
- **SQLAlchemy + Alembic** (persistência das configurações)
- **SQLite FTS5** (índice de busca do conteúdo do Diário Oficial)
- **Poppler-utils** (`pdfinfo`, `pdftotext`) para extração de texto de PDF
- **Flask-Mail** para envio de e-mails
- **Redis + RQ** (opcional) para processamento assíncrono
- **Docker + Gunicorn** para produção

### Estrutura de diretórios

```text
notificador-iof-mg/
├── app/                 # App Flask (UI + API)
│   ├── api/             # Endpoints REST
│   ├── web/             # Rotas HTML (Jinja2)
│   ├── models/          # Modelos SQLAlchemy (SearchConfig/SearchTerm)
│   ├── services/        # Regras de negócio (SearchService)
│   ├── tasks/           # Processamento do diário / notificações (RQ opcional)
│   ├── templates/       # HTML (Tailwind via CDN)
│   └── static/          # JS/CSS
├── iof/                 # Cliente para API v1 do Jornal Minas Gerais
├── pdf/                 # Extração de texto de PDFs (poppler-utils)
├── search/              # Motor de busca (SQLite FTS5)
├── mailer/              # Envio de e-mails + template + CSV
├── migrations/          # Alembic migrations (config DB)
├── Dockerfile           # Imagem de produção
├── entrypoint.sh        # Startup: diretórios + migrations + gunicorn
└── .github/workflows/   # CI/CD (deploy Azure)
```

---

## 🗄️ Persistência (IMPORTANTE)

Este projeto usa **dois bancos/artefatos diferentes**:

1) **Banco de Configuração (SQLAlchemy/Alembic)**
- Guarda as configurações de busca e termos (`SearchConfig`/`SearchTerm`).
- Por padrão usa **SQLite** (`DATABASE_URL` default), mas pode usar **PostgreSQL**.

2) **Banco de Índice de Busca (SQLite FTS5)**
- Arquivo **`diarios.db`** dentro de `DIARIOS_DIR`.
- Armazena o conteúdo extraído por página e cria índice FTS para busca rápida.

> Em produção no Azure App Service (container), recomenda-se persistir em `/home`.

---

## ✅ Requisitos

- **Python 3.13+** (ver `.python-version`)
- **poppler-utils** (ou `poppler` no macOS) para `pdfinfo` e `pdftotext`
- (Opcional) **Redis** para RQ
- (Opcional) **PostgreSQL** em produção
- Docker (opcional para rodar container local / produção)

---

## ⚙️ Configuração via `.env`

A aplicação carrega variáveis de ambiente via `python-dotenv`.

### Template sugerido (`.env.example`)

> **Dica:** este repositório não inclui `.env.example` por padrão. Você pode criar o arquivo abaixo e manter **segredos fora do Git**.

```env
# Ambiente
APP_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Proteção do endpoint /api/tasks/process-daily
API_KEY=coloque-um-token-longo-aqui

# Persistência
# DIARIOS_DIR controla onde fica o diarios.db (FTS5)
DIARIOS_DIR=diarios
# DATABASE_URL controla o banco do SQLAlchemy (configs)
# SQLite (local):
DATABASE_URL=sqlite:///instance/local.db

# PostgreSQL (exemplo):
# DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME

# SMTP / Email
MAIL_FROM_ADDRESS=seu-email@gmail.com
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_SMTP_USER=seu-email@gmail.com
MAIL_SMTP_PASSWORD=sua-senha-de-app

# Redis (opcional - para RQ)
REDIS_URL=redis://localhost:6379/0

# Gunicorn (produção)
PORT=8000
GUNICORN_TIMEOUT=300
GUNICORN_WORKERS=2
LOG_LEVEL=info
```

### SMTP – exemplos rápidos

#### Gmail (recomendado)
- Use **Senha de App** (não a senha normal da conta).
- Porta recomendada: **587** com **TLS**.

#### MailHog (dev/local)
- Suba o MailHog e aponte para `localhost:1025`.

```env
MAIL_SMTP_HOST=localhost
MAIL_SMTP_PORT=1025
MAIL_USE_TLS=false
MAIL_USE_SSL=false
MAIL_SMTP_USER=
MAIL_SMTP_PASSWORD=
```

---

## 🧬 Banco de dados e migrations

### 1) Banco das configurações (SQLAlchemy/Alembic)

Para criar/atualizar as tabelas:

```bash
uv run alembic upgrade head
```

O `entrypoint.sh` também executa migrations automaticamente ao iniciar o container.

### 2) Banco de busca (SQLite FTS5)

O índice e tabelas do FTS5 são inicializados automaticamente pelo `SearchSource` com o SQL em `search/schema.sql`.

---

## ▶️ Executando localmente

### Desenvolvimento (recomendado)

```bash
# instalar deps
uv sync

# migrations
uv run alembic upgrade head

# subir servidor
uv run flask run

# ou
uv run python run.py
```

Acesse: http://localhost:5000

### Login com Microsoft Entra ID (DEV)

O login é feito apenas via **Microsoft Entra ID** (SSO). Não há formulário de e-mail/senha.

1. Configure no `.env` as variáveis Entra (veja `env.example.md`, seção **Entra ID (SSO)**): `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_AUTHORITY` (ou derivada de `ENTRA_TENANT_ID`), `ENTRA_REDIRECT_URI=http://localhost:5000/auth/callback`, `ENTRA_SCOPES=openid profile email`.
2. No portal Azure (Entra ID), registre a **Redirect URI** exata: `http://localhost:5000/auth/callback`.
3. Rode `uv run flask run` e acesse http://localhost:5000/login.
4. Clique em **Entrar com Microsoft**; após autenticar, você será redirecionado para `/auth/callback` e em seguida para a página inicial.

### Produção (Gunicorn)

```bash
uv run gunicorn --config gunicorn_config.py wsgi:application
```

---

## 🖥️ Interface Web (UI)

Rotas principais:

- `GET /` – lista configurações
- `GET|POST /configs/new` – criar
- `GET /configs/<id>` – detalhes
- `GET|POST /configs/<id>/edit` – editar
- `POST /configs/<id>/delete` – deletar
- `GET|POST /configs/<id>/backtest` – backtest (**somente em `APP_ENV=development`**)

### Como usar

1. Acesse a página inicial e clique em **“Nova Configuração”**.
2. Informe:
   - Nome
   - Descrição (opcional)
   - Termos (até 5)
   - Destinatários (até 5)
   - (Opcional) **Anexar CSV**
3. Salve.
4. (DEV) Use **“Testar Busca”** para validar em uma data específica.

---

## 🧩 API REST

### Features

- `GET /api/features`
  - Retorna features habilitadas (ex.: `backtest` somente em `development`).

### Configurações de busca (CRUD)

- `GET /api/search/configs?active_only=true|false`
- `POST /api/search/configs`
- `GET /api/search/configs/<id>`
- `PUT /api/search/configs/<id>`
- `DELETE /api/search/configs/<id>`
- `GET /api/search/configs/<id>/backtest?date=YYYY-MM-DD` (**DEV**)

### Tarefas (admin)

#### Processar diário (endpoint para agendamento)

- `POST /api/tasks/process-daily?api_key=<API_KEY>`

Body (opcional):

```json
{ "date": "2026-01-14" }
```

Exemplos:

```bash
# hoje
curl -X POST "http://localhost:5000/api/tasks/process-daily?api_key=$API_KEY"

# data específica
curl -X POST \
  "http://localhost:5000/api/tasks/process-daily?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-01-14"}'
```

> **Auth:** o backend aceita `api_key` via query string (recomendado) e também tenta `Authorization: Bearer ...` ou `X-API-Key`.

### Erros

A API retorna erros padronizados no formato:

```json
{
  "code": "validation_failed",
  "message": "Os dados informados são inválidos",
  "errors": {
    "campo": "motivo"
  }
}
```

---

## 🧰 Processamento assíncrono (RQ/Redis) – opcional

O código possui suporte a **Redis + RQ** para enfileirar as notificações por configuração.

### Quando usar

- Se você quiser separar o processamento em:
  - **Job 1:** baixar/importar páginas do diário
  - **Jobs N:** notificar cada configuração

### Como rodar (local)

1) Suba um Redis:

```bash
docker run -p 6379:6379 redis:7
```

2) Ajuste `REDIS_URL` no `.env`.

3) Inicie um worker RQ:

```bash
# exemplo: usar o entrypoint do rq (dependendo de como você preferir rodar)
uv run rq worker default
```

> **Observação:** o endpoint `/api/tasks/process-daily` possui uma versão síncrona (sem RQ) para simplificar o uso em produção sem Redis.

---

## 🐳 Docker

### Build

```bash
docker build -t notificador-iof-mg:local .
```

### Run (local)

> Para simular persistência, monte um volume para armazenar `diarios.db` e o `local.db`.

```bash
mkdir -p ./_data/diarios ./_data/instance

docker run --rm -p 8000:8000 \
  -e APP_ENV=production \
  -e API_KEY=seu_token \
  -e MAIL_SMTP_HOST=smtp.gmail.com \
  -e MAIL_SMTP_PORT=587 \
  -e MAIL_USE_TLS=true \
  -e MAIL_SMTP_USER=seu-email@gmail.com \
  -e MAIL_SMTP_PASSWORD=sua-senha-de-app \
  -e MAIL_FROM_ADDRESS=seu-email@gmail.com \
  -e DIARIOS_DIR=/home/diarios \
  -e DATABASE_URL=sqlite:////home/instance/local.db \
  -v "$(pwd)/_data/diarios:/home/diarios" \
  -v "$(pwd)/_data/instance:/home/instance" \
  notificador-iof-mg:local
```

Acesse: http://localhost:8000

### O que o `entrypoint.sh` faz

- Define diretórios persistentes (`/home/diarios` e `/home/instance`) quando aplicável
- Executa `alembic upgrade head`
- Inicializa tabelas caso necessário
- Sobe o Gunicorn

---

## ☁️ Deploy no Azure (App Service + ACR) + GitHub Actions (OIDC)

Este repositório já inclui workflow de deploy por container:

- `.github/workflows/deploy.yml`
  - Build da imagem Docker
  - Push para **Azure Container Registry (ACR)**
  - Atualiza `linuxFxVersion` do App Service para apontar para a imagem (tag = SHA)
  - Reinicia o Web App

### Secrets necessários no GitHub

Configure em **Settings → Secrets and variables → Actions**:

- `AZURE_WEB_APP_NAME`
- `AZURE_RESOURCE_GROUP`
- `AZURE_REGISTRY_NAME`
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

### Variáveis de ambiente no App Service

No **App Service → Configuration → Application settings**, configure (exemplos):

- `APP_ENV=production`
- `API_KEY=...`
- `MAIL_*` (SMTP)
- `DATABASE_URL=sqlite:////home/instance/local.db` (ou Postgres)
- `DIARIOS_DIR=/home/diarios`

E garanta:

- `WEBSITES_ENABLE_APP_SERVICE_STORAGE=true` (para persistir `/home`)

### Federated Credentials (OIDC)

O repo contém `credential.json` / `credential-noslash.json` como referência do *subject* do GitHub Actions para configurar **Workload Identity Federation**.

---

## 🔐 Segurança

- **Proteja o endpoint** `/api/tasks/process-daily` com `API_KEY`.
- Em produção, **mude** `SECRET_KEY`.
- Não commite `.env` nem segredos.
- O `entrypoint.sh` mascara credenciais no log quando `DATABASE_URL` inclui usuário/senha.

---

## 🧯 Troubleshooting

### 1) E-mail não envia

- Verifique `MAIL_SMTP_HOST`, `MAIL_SMTP_PORT`, `MAIL_SMTP_USER`, `MAIL_SMTP_PASSWORD`.
- Gmail: use **Senha de App** e `MAIL_USE_TLS=true` na porta **587**.
- Teste via Backtest (em `development`) para validar SMTP rapidamente.

### 2) Diário não encontrado

- Nem todas as datas têm publicação.
- A API do jornal pode não disponibilizar todas as edições.

### 3) Erro ao processar PDF

- Confirme que `pdfinfo` e `pdftotext` estão instalados e no `PATH`.
- No Docker, `poppler-utils` já é instalado na imagem.

### 4) Problemas de persistência no Azure

- Confirme `WEBSITES_ENABLE_APP_SERVICE_STORAGE=true`.
- Use caminhos em `/home` (ex.: `DATABASE_URL=sqlite:////home/instance/local.db` e `DIARIOS_DIR=/home/diarios`).

---

## 🧪 Desenvolvimento

### Padrão de evolução (roadmap)

- **Fase 1:** SQLite local + UI básica
- **Fase 2:** Jobs assíncronos com RQ
- **Fase 3:** Migração para PostgreSQL (opcional)

### Backtest

- Disponível apenas quando `APP_ENV=development`.

---

## 📄 Licença

Projeto de uso interno para notificações do Diário Oficial de Minas Gerais.
