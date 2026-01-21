# Solução: Erro "no such table: search_configs"

## Problema Identificado

O erro `sqlite3.OperationalError: no such table: search_configs` ocorre porque:

1. ✅ A migration existe e deveria criar as tabelas
2. ✅ A migration está sendo executada (logs mostram "Running upgrade -> 001")
3. ❌ Mas as tabelas não estão sendo criadas no banco correto

## Causa Raiz

O Flask cria o banco SQLite em `instance/local.db` por padrão quando usa `sqlite:///local.db`, mas:
- O diretório `instance` pode não existir no container
- A migration pode estar criando em um banco diferente
- O Alembic pode não estar usando a URL correta do banco

## Solução Aplicada

### 1. Correções no Código

**Arquivo: `entrypoint.sh`**
- Adicionado criação do diretório `instance`
- Adicionada verificação do banco após migrations

**Arquivo: `migrations/env.py`**
- Corrigido para usar a URL do banco do Flask app context
- Garantido que a migration usa o mesmo banco que a aplicação

### 2. Como Corrigir o Container Atual

Execute o script de correção:

```bash
./fix-database.sh
```

Ou manualmente:

```bash
# 1. Criar diretório instance
docker exec notificador-iof-mg mkdir -p /app/instance

# 2. Executar migrations novamente
docker exec notificador-iof-mg alembic upgrade head

# 3. Reiniciar container
docker restart notificador-iof-mg
```

### 3. Rebuild da Imagem (Recomendado)

Para garantir que o problema não ocorra novamente, faça rebuild da imagem:

```bash
# Parar e remover container atual
docker stop notificador-iof-mg
docker rm notificador-iof-mg

# Rebuild da imagem com as correções
docker build -t notificador-iof-mg:latest .

# Executar novamente
docker run -d \
  --name notificador-iof-mg \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/diarios:/app/diarios" \
  notificador-iof-mg:latest
```

### 4. Verificar se Funcionou

```bash
# Ver logs
docker logs notificador-iof-mg

# Verificar se banco foi criado
docker exec notificador-iof-mg ls -la /app/instance/

# Testar endpoint
curl http://localhost:8000/api/features

# Testar interface web
curl http://localhost:8000
```

## Próximos Passos

Após corrigir:

1. ✅ Verificar que `/api/features` funciona
2. ✅ Verificar que interface web (`/`) funciona sem erro 500
3. ✅ Verificar que rota de processamento funciona
4. ✅ **Pronto para FASE 2**: Deploy na Azure

## Nota sobre FASE 2

Este problema **NÃO** deve ocorrer na Azure porque:
- O banco será criado no caminho especificado pelo `DATABASE_URL`
- O diretório será criado automaticamente pelo sistema de arquivos
- As migrations serão executadas no mesmo ambiente

Você pode prosseguir para a FASE 2 após corrigir localmente, pois as correções já estão no código.
