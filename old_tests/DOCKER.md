# Guia de Build e Teste Docker (FASE 1)

Este documento explica como testar o container Docker localmente antes do deploy na Azure.

## Pré-requisitos

- Docker instalado
- Arquivo `.env` configurado (ou variáveis de ambiente)

## Build da Imagem

```bash
# Build da imagem
docker build -t notificador-iof-mg:latest .

# Ou com tag específica
docker build -t notificador-iof-mg:v1.0.0 .
```

## Executar Container Localmente

### 1. Preparar variáveis de ambiente

Crie um arquivo `.env` ou exporte as variáveis necessárias:

```bash
export APP_ENV=production
export SECRET_KEY=sua-chave-secreta-aqui
export API_KEY=seu-token-api-aqui
export DATABASE_URL=sqlite:///local.db
export DIARIOS_DIR=diarios
# ... outras variáveis
```

### 2. Executar container

```bash
# Executar com volume local para persistir banco de dados
docker run -d \
  --name notificador-iof-mg \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/diarios:/app/diarios \
  notificador-iof-mg:latest
```

### 3. Verificar logs

```bash
# Ver logs do container
docker logs -f notificador-iof-mg

# Ver últimas 50 linhas
docker logs --tail 50 notificador-iof-mg
```

### 4. Testar aplicação

```bash
# Testar endpoint de features
curl http://localhost:8000/api/features

# Testar interface web
# Abrir no navegador: http://localhost:8000
```

### 5. Testar rota de processamento (protegida)

```bash
# Substituir YOUR_API_KEY pelo token configurado
curl -X POST http://localhost:8000/api/tasks/process-daily \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}'

# Ou processar diário de hoje (sem especificar data)
curl -X POST http://localhost:8000/api/tasks/process-daily \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

## Comandos Úteis

```bash
# Parar container
docker stop notificador-iof-mg

# Iniciar container parado
docker start notificador-iof-mg

# Remover container
docker rm notificador-iof-mg

# Executar shell dentro do container
docker exec -it notificador-iof-mg /bin/bash

# Ver processos rodando
docker ps

# Ver uso de recursos
docker stats notificador-iof-mg
```

## Troubleshooting

### Erro: "Cannot connect to the Docker daemon"
- Verifique se o Docker está rodando: `docker ps`

### Erro: "Port already in use"
- Use outra porta: `-p 8001:8000`

### Erro: "Permission denied" no volume
- Ajuste permissões: `chmod 755 diarios`

### Migrations não executam
- Verifique logs: `docker logs notificador-iof-mg`
- Execute manualmente: `docker exec notificador-iof-mg alembic upgrade head`

### API Key não funciona
- Verifique se `API_KEY` está definida no `.env`
- Verifique logs para ver qual key está sendo esperada

## Próximos Passos

Após testar localmente e confirmar que tudo funciona:

1. ✅ Build da imagem funciona
2. ✅ Container inicia corretamente
3. ✅ Migrations executam
4. ✅ Aplicação responde na porta 8000
5. ✅ Rota de processamento funciona com autenticação
6. ✅ Banco de dados persiste no volume

**Pronto para FASE 2**: Criar recursos na Azure
