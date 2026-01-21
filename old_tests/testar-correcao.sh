#!/bin/bash
# Script para testar as correções aplicadas

set -e

echo "=== Testando Correções ==="
echo ""

# Parar container se estiver rodando
if docker ps | grep -q "notificador-iof-mg"; then
    echo "Parando container atual..."
    docker stop notificador-iof-mg
    docker rm notificador-iof-mg
fi

echo "1. Fazendo rebuild da imagem..."
docker build -t notificador-iof-mg:latest .

echo ""
echo "2. Executando container..."
docker run -d \
  --name notificador-iof-mg \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/diarios:/app/diarios" \
  notificador-iof-mg:latest

echo ""
echo "3. Aguardando inicialização (15 segundos)..."
sleep 15

echo ""
echo "4. Verificando logs..."
docker logs --tail 30 notificador-iof-mg

echo ""
echo "5. Testando endpoints..."
echo ""
echo "Testando /api/features..."
curl -s http://localhost:8000/api/features | python3 -m json.tool || echo "Erro"

echo ""
echo "Testando interface web (deve retornar HTML, não erro 500)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Interface web funcionando (HTTP 200)"
else
    echo "⚠ Interface web retornou HTTP $HTTP_CODE"
    echo "Verifique os logs para mais detalhes"
fi

echo ""
echo "=== Resumo ==="
echo "Se tudo estiver OK:"
echo "  - Logs mostram 'Migrations executadas'"
echo "  - /api/features retorna JSON"
echo "  - Interface web retorna HTTP 200"
echo ""
echo "Para ver logs em tempo real:"
echo "  docker logs -f notificador-iof-mg"
