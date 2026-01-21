#!/bin/bash
# Script para testar a API de processamento

echo "=== Teste da API de Processamento ==="
echo ""

# Obter API_KEY do .env
if [ -f .env ]; then
    API_KEY=$(grep "API_KEY=" .env | cut -d '=' -f2)
    if [ -z "$API_KEY" ]; then
        echo "❌ API_KEY não encontrada no .env"
        echo "Execute: echo 'API_KEY=seu-token-aqui' >> .env"
        exit 1
    fi
else
    echo "❌ Arquivo .env não encontrado"
    exit 1
fi

echo "1. Testando /api/features..."
curl -s http://localhost:8000/api/features | python3 -m json.tool
echo ""

echo "2. Testando /api/tasks/process-daily com API_KEY..."
echo "API_KEY usada: ${API_KEY:0:10}..."
echo ""

# Fazer requisição e capturar código HTTP e corpo separadamente
HTTP_CODE=$(curl -s -o /tmp/response_body.json -w "%{http_code}" -X POST http://localhost:8000/api/tasks/process-daily -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" -d '{"date": "2026-01-14"}')

echo "Resposta HTTP: $HTTP_CODE"
echo "Corpo da resposta:"
if [ -f /tmp/response_body.json ]; then
    cat /tmp/response_body.json | python3 -m json.tool 2>/dev/null || cat /tmp/response_body.json
    rm -f /tmp/response_body.json
else
    echo "(sem corpo)"
fi

echo ""
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Rota de processamento funcionando!"
elif [ "$HTTP_CODE" = "401" ]; then
    echo "❌ Erro de autenticação. Verifique se API_KEY está correta."
    echo "API_KEY no .env: ${API_KEY:0:20}..."
    echo ""
    echo "Para verificar a API_KEY no container:"
    echo "  docker exec notificador-iof-mg env | grep API_KEY"
else
    echo "⚠ Resposta HTTP $HTTP_CODE"
fi
