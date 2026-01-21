#!/bin/bash
# Script para reconstruir o container e testar a API

echo "=== Reconstruindo Container ==="
echo ""

# Parar e remover container existente
echo "1. Parando container existente..."
docker stop notificador-iof-mg 2>/dev/null || true
docker rm notificador-iof-mg 2>/dev/null || true

# Reconstruir imagem
echo "2. Reconstruindo imagem Docker..."
docker build -t notificador-iof-mg:latest .

if [ $? -ne 0 ]; then
    echo "❌ Erro ao construir imagem Docker"
    exit 1
fi

echo "✅ Imagem construída com sucesso"
echo ""

# Executar container
echo "3. Iniciando container..."
docker run -d \
  --name notificador-iof-mg \
  -p 8000:8000 \
  --env-file .env \
  notificador-iof-mg:latest

if [ $? -ne 0 ]; then
    echo "❌ Erro ao iniciar container"
    exit 1
fi

echo "✅ Container iniciado"
echo ""

# Aguardar container iniciar
echo "4. Aguardando container iniciar (10 segundos)..."
sleep 10

# Verificar logs
echo "5. Últimos logs do container:"
docker logs notificador-iof-mg --tail 20
echo ""

# Testar API
echo "6. Testando API com query parameter..."
./test-api-query.sh
