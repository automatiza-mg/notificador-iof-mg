# Guia de Testes - Notificador IOF MG

## Passo 1: Instalar Dependências

```bash
uv sync
```

Se ainda der erro, tente limpar o cache:
```bash
uv cache clean
uv sync
```

## Passo 2: Configurar Ambiente

```bash
cp env.example .env
# Edite o .env com suas configurações (pelo menos DATABASE_URL)
```

Para desenvolvimento com SQLite (mais simples):
```bash
# No .env, deixe:
DATABASE_URL=sqlite:///local.db
APP_ENV=development
```

## Passo 3: Testar Instalação Básica

```bash
uv run python test_install.py
```

Este script verifica se todos os módulos podem ser importados.

## Passo 4: Testar MVP 0 (Setup)

```bash
uv run python test_mvp0.py
```

Deve mostrar:
- ✅ Flask instalado
- ✅ app.create_app importado
- ✅ App criada

## Passo 5: Testar MVP 1 (Modelos)

```bash
uv run python test_mvp1.py
```

Este script:
- Cria o banco SQLite
- Cria as tabelas
- Insere dados de teste
- Verifica se os dados foram salvos

**Verificar manualmente:**
```bash
ls -lh local.db
# Deve existir um arquivo local.db
```

## Passo 6: Testar MVP 2 (PDF)

**Pré-requisito:** Instalar poppler-utils (opcional para teste básico)

O teste criará automaticamente um PDF de teste se não existir.

**Instalar poppler-utils (para extração completa):**

**macOS:**
```bash
brew install poppler
```

**Linux:**
```bash
sudo apt-get install poppler-utils
```

**Verificar instalação:**
```bash
pdfinfo -v
pdftotext -v
```

**Teste:**
```bash
uv run python test_mvp2.py
```

**Nota:** O teste passará mesmo sem poppler-utils instalado, mas não conseguirá extrair texto do PDF. Para testar a extração completa, instale poppler-utils primeiro.

## Passo 7: Testar MVP 3 (Busca)

```bash
uv run python test_mvp3.py
```

Este script:
- Cria banco de busca SQLite
- Importa páginas de teste
- Executa busca
- Verifica resultados

**Verificar:**
```bash
ls -lh search_test.db
```

## Passo 8: Testar API (V1)

**Terminal 1 - Servidor:**
```bash
uv run python run.py
# ou
uv run flask run
```

**Terminal 2 - Testes:**
```bash
# 1. Listar configurações (deve retornar vazio ou dados)
curl http://localhost:5000/api/search/configs

# 2. Criar configuração
curl -X POST http://localhost:5000/api/search/configs \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Teste API",
    "description": "Configuração de teste",
    "attach_csv": false,
    "mail_to": ["teste@example.com"],
    "mail_subject": "Teste",
    "terms": [{"term": "teste", "exact": false}]
  }'

# 3. Listar novamente (deve mostrar a config criada)
curl http://localhost:5000/api/search/configs

# 4. Buscar por ID (substitua 1 pelo ID retornado)
curl http://localhost:5000/api/search/configs/1
```

## Passo 9: Testar Features API

```bash
curl http://localhost:5000/api/features
```

Deve retornar:
```json
{"backtest": true}
```

## Passo 10: Testar Backtest (V3)

**Pré-requisito:** Ter credenciais IOF no .env

```bash
# 1. Criar configuração (se ainda não tiver)
CONFIG_ID=1  # Ajustar com ID real

# 2. Testar backtest (ajustar data para uma data com diário disponível)
curl "http://localhost:5000/api/search/configs/$CONFIG_ID/backtest?date=2025-01-15"
```

## Passo 11: Testar Workers RQ (V6)

**Pré-requisito:** Redis rodando

**Instalar Redis (macOS):**
```bash
brew install redis
brew services start redis
```

**Terminal 1 - Worker:**
```bash
uv run rq worker --with-scheduler
```

**Terminal 2 - Enfileirar job:**
```bash
uv run python << EOF
from app.tasks.daily_gazette import process_daily_gazette
from datetime import date

process_daily_gazette(date.today())
print("Job executado")
EOF
```

## Troubleshooting

### Erro: "Unable to determine which files to ship"
✅ **Resolvido** - Adicionei `[tool.hatch.build.targets.wheel]` no pyproject.toml

### Erro: "Module not found"
- Verifique se executou `uv sync`
- Verifique se está usando `uv run python` ou `uv run flask`

### Erro: "Database connection failed"
- Verifique `DATABASE_URL` no `.env`
- Para SQLite, use: `sqlite:///local.db`
- Para PostgreSQL, use: `postgresql://user:pass@host/dbname`

### Erro: "poppler-utils not found"
- Instale poppler-utils (veja Passo 6)

### Erro: "Redis connection failed"
- Verifique se Redis está rodando: `redis-cli ping`
- Verifique `REDIS_URL` no `.env`

## Ordem Recomendada de Testes

1. ✅ `uv sync` - Instalar dependências
2. ✅ `test_install.py` - Verificar imports
3. ✅ `test_mvp0.py` - Setup básico
4. ✅ `test_mvp1.py` - Modelos e banco
5. ✅ `test_mvp2.py` - Extração PDF (opcional se não tiver PDF)
6. ✅ `test_mvp3.py` - Busca FTS5
7. ✅ API manual com curl
8. ✅ Backtest (requer credenciais IOF)
9. ✅ Workers RQ (requer Redis)
