#!/bin/bash
# Teste final da API - usando header correto

echo "=== Teste Final da API ==="
echo ""

# Obter API_KEY
if [ -f .env ]; then
    API_KEY=$(grep "^API_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    if [ -z "$API_KEY" ]; then
        echo "❌ API_KEY não encontrada no .env"
        exit 1
    fi
else
    echo "❌ Arquivo .env não encontrado"
    exit 1
fi

echo "API_KEY: ${API_KEY:0:10}..."
echo ""

echo "1. Testando /api/features (deve funcionar):"
curl -s http://localhost:8000/api/features | python3 -m json.tool
echo ""

echo "2. Testando /api/tasks/process-daily SEM API_KEY (deve retornar 401):"
curl -s -w "\nHTTP: %{http_code}\n" -X POST http://localhost:8000/api/tasks/process-daily \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14}'
echo ""

echo "3. Testando /api/tasks/process-daily COM API_KEY e data válida:"
# Usar variável para garantir que o header seja exatamente X-API-Key (camelCase)
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X POST http://localhost:8000/api/tasks/process-daily \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"date": "2026-01-14"}')

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed 's/HTTP_CODE:[0-9]*//g')

echo "HTTP Code: $HTTP_CODE"
echo "Response Body:"
if [ -n "$BODY" ]; then
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "(vazio)"
fi

echo ""
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCESSO! A API está funcionando corretamente!"
elif [ "$HTTP_CODE" = "401" ]; then
    echo "❌ Erro de autenticação. Verifique se API_KEY está correta."
    echo "   API_KEY no .env: ${API_KEY:0:20}..."
    echo "   Para verificar no container: docker exec notificador-iof-mg env | grep API_KEY"
elif [ "$HTTP_CODE" = "400" ]; then
    echo "⚠ HTTP 400 - Bad Request"
    echo "   Verifique os logs do container: docker logs notificador-iof-mg --tail 20"
elif [ "$HTTP_CODE" = "500" ]; then
    echo "⚠ HTTP 500 - Erro interno (pode ser normal se houver erro no processamento)"
    echo "   Verifique os logs: docker logs notificador-iof-mg --tail 30"
else
    echo "⚠ Resposta HTTP $HTTP_CODE"
fi
