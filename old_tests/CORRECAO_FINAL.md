# Correção Final - Problema de Tabelas

## Problema

A migration executa mas as tabelas não são criadas porque:
1. O Flask SQLAlchemy cria o banco em `instance/local.db` por padrão
2. O Alembic pode estar usando um caminho diferente
3. O diretório `instance` pode não existir quando a migration roda

## Correções Aplicadas

### 1. `app/config.py`
- Cria o diretório `instance` automaticamente
- Converte `sqlite:///local.db` para caminho absoluto `sqlite:///app/instance/local.db`
- Garante que Flask e Alembic usem o mesmo caminho

### 2. `app/utils/db_init.py` (novo)
- Fallback que cria tabelas usando `db.create_all()` se não existirem
- Executado na inicialização da aplicação

### 3. `app/__init__.py`
- Chama `init_db()` após criar a app
- Garante que tabelas existam mesmo se migrations falharem

## Como Aplicar

### Opção 1: Rebuild Completo (Recomendado)

```bash
# Parar e remover container
docker stop notificador-iof-mg
docker rm notificador-iof-mg

# Rebuild
docker build -t notificador-iof-mg:latest .

# Executar
docker run -d \
  --name notificador-iof-mg \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/diarios:/app/diarios" \
  notificador-iof-mg:latest

# Verificar logs
docker logs -f notificador-iof-mg
```

### Opção 2: Aplicar Correção no Container Atual

```bash
# Executar dentro do container para criar tabelas manualmente
docker exec notificador-iof-mg python3 -c "
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Tabelas criadas!')
"

# Reiniciar
docker restart notificador-iof-mg
```

## Verificação

Após aplicar, verifique:

```bash
# 1. Ver logs - deve mostrar "Tabelas criadas" ou similar
docker logs notificador-iof-mg | grep -i "tabela\|table"

# 2. Testar endpoint
curl http://localhost:8000/api/features

# 3. Testar interface web (não deve dar erro 500)
curl http://localhost:8000
```

## Próximos Passos

Após confirmar que funciona:
- ✅ **FASE 1 completa**
- ✅ **Pronto para FASE 2**: Deploy na Azure
