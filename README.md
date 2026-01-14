# Notificador IOF MG

Sistema de notificações do Diário Oficial de Minas Gerais.

## Requisitos

- Python 3.13+
- [UV Python](https://github.com/astral-sh/uv) - Gerenciador de pacotes
- [poppler-utils](https://poppler.freedesktop.org/) - Para extração de texto de PDFs

### Instalação do poppler-utils

**macOS:**
```bash
brew install poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install poppler-utils
```

## Configuração

1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Edite o arquivo `.env` com suas configurações.

3. Instale as dependências:
```bash
uv sync
```

## Executando

```bash
# Executar servidor Flask
uv run flask run

# Executar comando Python
uv run python script.py
```

## Estrutura do Projeto

```
notificador-iof-mg/
├── app/              # Aplicação Flask
├── migrations/       # Migrations do banco (Alembic)
├── search/           # Motor de busca SQLite FTS5
├── iof/              # Cliente Diário Oficial
├── pdf/              # Extração de PDF
├── mailer/           # Envio de emails
└── tests/            # Testes
```

## Desenvolvimento

Este projeto segue uma abordagem MVP incremental:
- Começa simples (SQLite local)
- Evolui gradualmente (PostgreSQL, RQ, etc.)
- Cada fase tem checkpoints de teste obrigatórios

