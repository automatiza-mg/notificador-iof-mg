# Correção: Problema de Ordem de Execução

## Problema Identificado

O erro `table search_configs already exists` ocorria porque:

1. **Ordem de execução problemática:**
   - Quando o Alembic importa `app` em `migrations/env.py`, ele chama `create_app()`
   - `create_app()` estava chamando `init_db()` que criava as tabelas usando `db.create_all()`
   - Depois, o Alembic tentava executar a migration que também tentava criar as tabelas
   - Resultado: **"table search_configs already exists"**

## Correções Aplicadas

### 1. `app/__init__.py`
- ✅ **Removido** `init_db()` da função `create_app()`
- Agora a app não cria tabelas automaticamente na inicialização
- As tabelas são criadas apenas pelas migrations do Alembic

### 2. `migrations/versions/001_create_search_tables.py`
- ✅ **Adicionada verificação** se as tabelas já existem antes de criar
- Usa `inspector.get_table_names()` para verificar
- Só cria tabelas se não existirem
- Evita erro se `db.create_all()` tiver criado as tabelas antes

### 3. `entrypoint.sh`
- ✅ **Adicionado fallback** que verifica e cria tabelas após migrations
- Se migrations não criarem (por algum motivo), o fallback cria
- Garante que as tabelas sempre existam

## Como Testar

```bash
# 1. Parar e remover container atual
docker stop notificador-iof-mg
docker rm notificador-iof-mg

# 2. Rebuild com as correções
docker build -t notificador-iof-mg:latest .

# 3. Executar novamente
docker run -d \
  --name notificador-iof-mg \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/diarios:/app/diarios" \
  notificador-iof-mg:latest

# 4. Verificar logs (aguarde ~15 segundos)
docker logs -f notificador-iof-mg
```

## O que Procurar nos Logs

✅ **Sucesso esperado:**
```
=== Iniciando Notificador IOF MG ===
Executando migrations do banco de dados...
INFO  [alembic.runtime.migration] Running upgrade  -> 001, create search tables
✓ Migrations executadas com sucesso
✓ Banco de dados criado em /app/instance/local.db
Iniciando servidor Gunicorn...
Listening at: http://0.0.0.0:8000
```

❌ **Se ainda houver erro:**
- Verifique se o banco antigo não está sendo reutilizado
- Remova o volume: `rm -rf instance/` (localmente)
- Rebuild sem cache: `docker build --no-cache -t notificador-iof-mg:latest .`

## Teste Rápido

Após o container iniciar:

```bash
# Testar API
curl http://localhost:8000/api/features

# Testar interface web (não deve dar erro 500)
curl -I http://localhost:8000
# Deve retornar HTTP 200
```

## Próximos Passos

Após confirmar que funciona:
- ✅ **FASE 1 completa**
- ✅ **Pronto para FASE 2**: Deploy na Azure
