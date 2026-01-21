# Guia Passo a Passo - Teste Local Docker (FASE 1)

Siga estes passos para testar o container Docker localmente.

## Pré-requisitos

1. ✅ Docker Desktop instalado e rodando
2. ✅ Arquivo `.env` configurado (ou será criado automaticamente)

## Passo 1: Preparar Variáveis de Ambiente

### Opção A: Usar o script automatizado

```bash
./test-docker.sh
```

O script irá:
- Verificar se Docker está rodando
- Criar/verificar arquivo `.env`
- Gerar `API_KEY` e `SECRET_KEY` automaticamente
- Fazer build da imagem
- Executar o container
- Testar os endpoints

### Opção B: Manual

1. **Verificar/criar arquivo `.env`:**

```bash
# Se não existir, copiar do exemplo
cp env.example .env
```

2. **Adicionar variáveis de segurança ao `.env`:**

```bash
# Gerar API_KEY e SECRET_KEY
python3 -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

Adicione as linhas geradas ao final do arquivo `.env`:

```env
API_KEY=seu-token-gerado-aqui
SECRET_KEY=sua-chave-secreta-gerada-aqui
APP_ENV=production
```

**⚠️ IMPORTANTE**: Anote a `API_KEY` gerada, você precisará dela para testar a rota de processamento!

## Passo 2: Build da Imagem Docker

```bash
# Fazer build da imagem (pode demorar alguns minutos na primeira vez)
docker build -t notificador-iof-mg:latest .
```

**O que está acontecendo:**
- Baixa imagem base Python 3.13-slim
- Instala poppler-utils
- Instala UV e dependências Python
- Copia código da aplicação
- Configura entrypoint

**Tempo estimado**: 3-5 minutos (primeira vez)

## Passo 3: Executar o Container

```bash
# Criar diretório para persistir banco de dados
mkdir -p diarios

# Executar container
docker run -d \
  --name notificador-iof-mg \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/diarios:/app/diarios" \
  notificador-iof-mg:latest
```

**O que está acontecendo:**
- Container inicia em background (`-d`)
- Porta 8000 do container mapeada para localhost:8000
- Variáveis de ambiente carregadas do `.env`
- Volume montado para persistir `diarios.db`

## Passo 4: Verificar Logs

```bash
# Ver logs em tempo real
docker logs -f notificador-iof-mg

# Ou ver últimas 50 linhas
docker logs --tail 50 notificador-iof-mg
```

**O que procurar nos logs:**
- ✅ `Executando migrations do banco de dados...`
- ✅ `✓ Migrations executadas com sucesso`
- ✅ `Iniciando servidor Gunicorn...`
- ✅ `Listening at: http://0.0.0.0:8000`

**Se houver erros:**
- Verifique se todas as variáveis de ambiente estão corretas
- Verifique se a porta 8000 não está em uso: `lsof -i :8000`

## Passo 5: Testar Endpoints

### 5.1. Testar API de Features

```bash
curl http://localhost:8000/api/features
```

**Resposta esperada:**
```json
{
  "features": [
    "Busca por termos",
    "Notificações por email",
    "Anexo CSV",
    "Interface web",
    "Backtest",
    "Busca FTS5",
    "API REST"
  ]
}
```

### 5.2. Testar Interface Web

Abra no navegador:
```
http://localhost:8000
```

Você deve ver a interface web do sistema.

### 5.3. Testar Rota de Processamento (Protegida)

**⚠️ IMPORTANTE**: Use a `API_KEY` que você gerou/anotou no Passo 1!

```bash
# Substituir YOUR_API_KEY pela sua API_KEY
curl -X POST http://localhost:8000/api/tasks/process-daily \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}'
```

**Resposta esperada (sucesso):**
```json
{
  "success": true,
  "message": "Diário de 2026-01-14 processado com sucesso",
  "date": "2026-01-14"
}
```

**Resposta esperada (sem autenticação):**
```json
{
  "success": false,
  "error": "Header X-API-Key não fornecido"
}
```

**Resposta esperada (API key inválida):**
```json
{
  "success": false,
  "error": "API Key inválida"
}
```

### 5.4. Processar Diário de Hoje (sem especificar data)

```bash
curl -X POST http://localhost:8000/api/tasks/process-daily \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

## Passo 6: Verificar Persistência do Banco

```bash
# Verificar se o arquivo diarios.db foi criado
ls -lh diarios/

# Ver conteúdo do banco (se tiver sqlite3 instalado)
sqlite3 diarios/diarios.db ".tables"
```

O arquivo `diarios/diarios.db` deve existir e persistir mesmo após reiniciar o container.

## Comandos Úteis

### Gerenciar Container

```bash
# Parar container
docker stop notificador-iof-mg

# Iniciar container parado
docker start notificador-iof-mg

# Reiniciar container
docker restart notificador-iof-mg

# Ver status
docker ps | grep notificador-iof-mg

# Remover container (para começar do zero)
docker rm -f notificador-iof-mg
```

### Ver Logs

```bash
# Logs em tempo real
docker logs -f notificador-iof-mg

# Últimas 100 linhas
docker logs --tail 100 notificador-iof-mg

# Logs desde um tempo específico
docker logs --since 10m notificador-iof-mg
```

### Executar Comandos Dentro do Container

```bash
# Abrir shell no container
docker exec -it notificador-iof-mg /bin/bash

# Executar migrations manualmente
docker exec notificador-iof-mg alembic upgrade head

# Verificar variáveis de ambiente
docker exec notificador-iof-mg env | grep API_KEY
```

### Rebuild da Imagem

```bash
# Se você modificou o código, fazer rebuild
docker build -t notificador-iof-mg:latest .

# Parar e remover container antigo
docker stop notificador-iof-mg
docker rm notificador-iof-mg

# Executar novamente
docker run -d \
  --name notificador-iof-mg \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/diarios:/app/diarios" \
  notificador-iof-mg:latest
```

## Troubleshooting

### Erro: "Cannot connect to the Docker daemon"

**Solução**: Inicie o Docker Desktop

```bash
# Verificar se Docker está rodando
docker info
```

### Erro: "Port 8000 is already allocated"

**Solução**: Use outra porta ou pare o processo que está usando a porta 8000

```bash
# Ver o que está usando a porta 8000
lsof -i :8000

# Ou usar outra porta
docker run -d \
  --name notificador-iof-mg \
  -p 8001:8000 \
  ...
```

### Erro: "No such file or directory: entrypoint.sh"

**Solução**: Verifique se o arquivo existe e tem permissão de execução

```bash
ls -la entrypoint.sh
chmod +x entrypoint.sh
```

### Erro nas Migrations

**Solução**: Execute manualmente dentro do container

```bash
docker exec notificador-iof-mg alembic upgrade head
```

### Container para de funcionar

**Solução**: Verifique os logs para identificar o erro

```bash
docker logs notificador-iof-mg
```

### API Key não funciona

**Solução**: 
1. Verifique se a `API_KEY` no `.env` está correta
2. Verifique se está usando a mesma key no header `X-API-Key`
3. Reinicie o container após alterar `.env`

```bash
# Ver API_KEY configurada no container
docker exec notificador-iof-mg env | grep API_KEY

# Reiniciar após alterar .env
docker restart notificador-iof-mg
```

### Erro: "ModuleNotFoundError"

**Solução**: O projeto pode não ter sido instalado corretamente. Rebuild a imagem:

```bash
docker build --no-cache -t notificador-iof-mg:latest .
```

## Checklist de Validação

Antes de prosseguir para a FASE 2, confirme:

- [ ] ✅ Build da imagem Docker funciona sem erros
- [ ] ✅ Container inicia e fica rodando
- [ ] ✅ Logs mostram "Migrations executadas com sucesso"
- [ ] ✅ Logs mostram "Listening at: http://0.0.0.0:8000"
- [ ] ✅ Endpoint `/api/features` responde corretamente
- [ ] ✅ Interface web acessível em `http://localhost:8000`
- [ ] ✅ Rota `/api/tasks/process-daily` funciona com `X-API-Key` correto
- [ ] ✅ Arquivo `diarios/diarios.db` é criado e persiste
- [ ] ✅ Container reinicia corretamente após `docker restart`

## Próximo Passo

Após validar todos os itens acima, você está pronto para a **FASE 2**: Criar recursos na Azure.

Consulte o arquivo `AZURE_DEPLOY.md` para instruções detalhadas.
