# Notificador IOF MG

> Sistema de notificações do **Diário Oficial de Minas Gerais (Jornal Minas Gerais)**: você cadastra termos de interesse e recebe **alertas por e-mail** quando esses termos aparecem no Diário Oficial.

## ✨ Principais funcionalidades

- 🔎 **Busca por termos (até 5 por configuração)**
  - Busca **exata** por termo ou expressão
- 📬 **Notificações por e-mail (até 5 destinatários)**
  - Assunto configurável por configuração
- 📎 **Anexo CSV opcional** com todos os resultados encontrados (compatível com Excel)
- 🌐 **Interface Web** para CRUD de configurações (criar/editar/ativar/desativar/deletar)
- 🧪 **Backtest**: testar configurações em datas específicas antes de ativar
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

# crie manualmente um arquivo .env usando o bloco documentado em env.example.md
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
                 - Busca termos de forma exata
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
- **Azure Communication Services Email** para envio em produção
- **Flask-Mail / SMTP** para desenvolvimento local
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

### Template sugerido para o `.env`

> **Dica:** use o arquivo `env.example.md` como referência documentada para montar seu `.env` local e manter **segredos fora do Git**.

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

# Email
APP_BASE_URL=http://localhost:5000
MAIL_PROVIDER=azure
AZURE_EMAIL_ENDPOINT=https://automatiza-comms.brazil.communication.azure.com/
AZURE_EMAIL_SENDER_ADDRESS=DoNotReply@SEU-DOMINIO.azurecomm.net
AZURE_COMMUNICATION_CONNECTION_STRING=endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=troque-esta-chave

# SMTP (dev/local)
MAIL_FROM_ADDRESS=noreply@local
MAIL_SMTP_HOST=localhost
MAIL_SMTP_PORT=1025
MAIL_USE_TLS=false
MAIL_USE_SSL=false
MAIL_SMTP_USER=
MAIL_SMTP_PASSWORD=

# Redis (opcional - para RQ)
REDIS_URL=redis://localhost:6379/0

# Gunicorn (produção)
PORT=8000
GUNICORN_TIMEOUT=300
GUNICORN_WORKERS=2
LOG_LEVEL=info
```

### Email – provedores suportados

#### Azure Email (produção)
- Provider padrão em `APP_ENV=production`.
- Requer:
  - `APP_BASE_URL`
  - `MAIL_PROVIDER=azure`
  - `AZURE_EMAIL_ENDPOINT`
  - `AZURE_EMAIL_SENDER_ADDRESS`
  - `AZURE_COMMUNICATION_CONNECTION_STRING`
- Os emails de alerta incluem um link individual de descadastro no rodapé.
- Se o último destinatário for removido por esse link, o alerta é inativado automaticamente.

#### SMTP / Flask-Mail (dev/local)
- Provider padrão em `development`.
- Use MailHog para desenvolvimento local:

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

#### Gmail (fallback de desenvolvimento)
- Use **Senha de App** e mantenha isso apenas fora da produção.

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
- `GET|POST /configs/<id>/backtest` – backtest da configuração

### Como usar

1. Acesse a página inicial e clique em **“Nova Configuração”**.
2. Informe:
   - Nome
   - Termos (até 5)
   - Destinatários (até 5)
   - (Opcional) **Anexar CSV**
3. Salve.
4. Em `APP_ENV=development`, o botão **“TESTAR”** aparece na tela de edição para validar em uma data específica.

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
  -e MAIL_PROVIDER=azure \
  -e AZURE_EMAIL_ENDPOINT=https://automatiza-comms.brazil.communication.azure.com/ \
  -e AZURE_EMAIL_SENDER_ADDRESS=DoNotReply@SEU-DOMINIO.azurecomm.net \
  -e AZURE_COMMUNICATION_CONNECTION_STRING='endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=SEU_ACCESS_KEY' \
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

## ☁️ Deploy na Azure (Hand-off para DevOps)

A infraestrutura foi desenhada para rodar em um **Azure App Service (Linux Web App for Containers)** utilizando uma imagem gerada via **Azure Container Registry (ACR)**. O deploy é totalmente contínuo via GitHub Actions usando **OIDC (Workload Identity Federation)**, eliminando a necessidade de secrets de senha.

### 1. Recursos necessários na Azure
O engenheiro de cloud precisará provisionar:
1. **Resource Group**: Para agrupar todos os recursos.
2. **Azure Container Registry (ACR)**: Para armazenar as imagens Docker.
3. **App Service Plan (Linux)**: Plano de hospedagem (Ex: B1 ou P1v3).
4. **Web App for Containers**: Onde o container irá rodar.
5. *(Opcional)* **Azure Storage Account**: Caso decidam usar um File Share montado ao invés do `/home` nativo do App Service.
6. *(Opcional)* **Azure Database for PostgreSQL**: Caso não queiram usar o SQLite no `/home`.

### 2. Configuração do OIDC (GitHub <-> Azure)
No Entra ID (Azure AD), crie uma **User Assigned Managed Identity** (ou App Registration) e configure as credenciais federadas apontando para este repositório do GitHub (branch `main`). 
Conceda a esta identidade as roles de `AcrPush` (no Container Registry) e `Website Contributor` (no Web App).

### 3. Secrets do GitHub Actions
Cadastre os seguintes repositórios em *Settings > Secrets and variables > Actions*:
- `AZURE_CLIENT_ID`: Client ID da Managed Identity/App.
- `AZURE_TENANT_ID`: Tenant ID do diretório.
- `AZURE_SUBSCRIPTION_ID`: ID da Assinatura.
- `AZURE_REGISTRY_NAME`: Nome do seu ACR (ex: `meuregistro`).
- `AZURE_WEB_APP_NAME`: Nome do seu Web App.
- `AZURE_RESOURCE_GROUP`: Nome do Resource Group do Web App.

### 4. Application Settings (Variáveis de Produção no Azure)
No painel do Azure Web App, vá em **Environment Variables** e adicione:
- `APP_ENV=production`
- `WEBSITES_ENABLE_APP_SERVICE_STORAGE=true` *(CRÍTICO: Garante que a pasta /home sobreviva a reboots)*
- `DIARIOS_DIR=/home/diarios`
- `DATABASE_URL=sqlite:////home/instance/local.db`
- `API_KEY=<token_seguro_para_o_cron>`
- `MAIL_PROVIDER=azure`
- `AZURE_EMAIL_ENDPOINT=<endpoint-do-acs>`
- `AZURE_EMAIL_SENDER_ADDRESS=<sender-address-autorizado>`
- `AZURE_COMMUNICATION_CONNECTION_STRING=<connection-string-do-acs>`
- Variáveis do Entra ID (`ENTRA_CLIENT_ID`, etc)

---

## 🔐 Segurança

- **Proteja o endpoint** `/api/tasks/process-daily` com `API_KEY`.
- Em produção, **mude** `SECRET_KEY`.
- Não commite `.env` nem segredos.
- O `entrypoint.sh` mascara credenciais no log quando `DATABASE_URL` inclui usuário/senha.

---

## 🧯 Troubleshooting

### 1) E-mail não envia

- Em produção (`MAIL_PROVIDER=azure`), verifique `AZURE_EMAIL_ENDPOINT`, `AZURE_EMAIL_SENDER_ADDRESS` e `AZURE_COMMUNICATION_CONNECTION_STRING`.
- Confirme que o `AZURE_EMAIL_SENDER_ADDRESS` pertence ao domínio provisionado no Azure Communication Services.
- Em desenvolvimento (`MAIL_PROVIDER=smtp`), verifique `MAIL_SMTP_HOST`, `MAIL_SMTP_PORT`, `MAIL_SMTP_USER` e `MAIL_SMTP_PASSWORD`.
- Gmail: use **Senha de App** e `MAIL_USE_TLS=true` na porta **587**.
- Teste via Backtest para validar o provider configurado rapidamente.

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

- Em `APP_ENV=development`, a interface exibe o botão **TESTAR** na tela de edição do alerta.
- A API de backtest continua restrita ao uso em desenvolvimento.

---

## 📄 Licença

Projeto de uso interno para notificações do Diário Oficial de Minas Gerais.
