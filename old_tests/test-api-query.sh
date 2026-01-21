#!/bin/bash
# Teste usando query parameter (recomendado para Gunicorn)

echo "=== Teste com Query Parameter (api_key) ==="
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

echo "2. Testando /api/tasks/process-daily SEM api_key (deve retornar 401):"
curl -s -w "\nHTTP: %{http_code}\n" -X POST http://localhost:8000/api/tasks/process-daily \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14}'
echo ""

echo "3. Testando /api/tasks/process-daily COM api_key no query parameter:"
# Testar primeiro se o container está respondendo
echo "   Verificando se container está rodando..."
if ! curl -s http://localhost:8000/api/features > /dev/null 2>&1; then
    echo "   ❌ Container não está respondendo!"
    echo "   Execute: docker logs notificador-iof-mg --tail 20"
    exit 1
fi
echo "   ✅ Container está respondendo"
echo ""

# Fazer requisição e salvar resposta em arquivo temporário
TMP_FILE=$(mktemp)
HTTP_CODE=$(curl -s -o "$TMP_FILE" -w "%{http_code}" \
  -X POST "http://localhost:8000/api/tasks/process-daily?api_key=${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}')

BODY=$(cat "$TMP_FILE" 2>/dev/null || echo "")
rm -f "$TMP_FILE"

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
    echo ""
    echo "Para usar no Azure Logic App, use:"
    echo "  URL: https://seu-app.azurewebsites.net/api/tasks/process-daily?api_key=${API_KEY:0:10}..."
    echo "  Method: POST"
    echo "  Body: {\"date\": \"2026-01-14\"}"
elif [ "$HTTP_CODE" = "401" ]; then
    echo "❌ Erro de autenticação. Verifique se API_KEY está correta."
elif [ "$HTTP_CODE" = "400" ]; then
    echo "⚠ HTTP 400 - Bad Request"
    echo "   Verifique os logs: docker logs notificador-iof-mg --tail 20"
elif [ "$HTTP_CODE" = "500" ]; then
    echo "⚠ HTTP 500 - Erro interno (pode ser normal se houver erro no processamento)"
    echo "   Verifique os logs: docker logs notificador-iof-mg --tail 30"
    echo ""
    echo "✅ Mas a autenticação funcionou! O erro 500 é do processamento, não da API."
else
    echo "⚠ Resposta HTTP $HTTP_CODE"
fi
