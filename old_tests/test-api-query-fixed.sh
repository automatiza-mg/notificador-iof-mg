#!/bin/bash
# Teste usando query parameter (versão corrigida)

echo "=== Teste com Query Parameter (api_key) ==="
echo ""

# Verificar se container está rodando
if ! docker ps | grep -q notificador-iof-mg; then
    echo "❌ Container não está rodando!"
    echo "Execute: docker start notificador-iof-mg"
    exit 1
fi

echo "✅ Container está rodando"
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
  -d '{"date": "2026-01-14"}'
echo ""

echo "3. Testando /api/tasks/process-daily COM api_key no query parameter:"
# Usar URL encoding para garantir que caracteres especiais sejam tratados corretamente
ENCODED_API_KEY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${API_KEY}'))")
URL="http://localhost:8000/api/tasks/process-daily?api_key=${ENCODED_API_KEY}"

echo "URL (primeiros 80 chars): ${URL:0:80}..."
echo ""

RESPONSE=$(curl -v -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}' \
  2>&1)

# Extrair HTTP code
HTTP_CODE=$(echo "$RESPONSE" | grep -oP '< HTTP/\d+\.\d+ \K\d+' | head -1)
if [ -z "$HTTP_CODE" ]; then
    HTTP_CODE=$(echo "$RESPONSE" | grep -oP 'HTTP/\d+\.\d+ \K\d+' | head -1)
fi

# Extrair body (tudo após a linha em branco após os headers)
BODY=$(echo "$RESPONSE" | awk '/^\r$/{getline; body=1} body')

echo "HTTP Code: ${HTTP_CODE:-'não encontrado'}"
echo "Response Body:"
if [ -n "$BODY" ]; then
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "(vazio ou erro de conexão)"
    echo ""
    echo "Resposta completa do curl (últimas 20 linhas):"
    echo "$RESPONSE" | tail -20
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
elif [ -z "$HTTP_CODE" ] || [ "$HTTP_CODE" = "000" ]; then
    echo "❌ Erro de conexão (HTTP 000)"
    echo "   Verificando status do container..."
    docker ps | grep notificador-iof-mg
    echo ""
    echo "   Logs recentes:"
    docker logs notificador-iof-mg --tail 10
else
    echo "⚠ Resposta HTTP $HTTP_CODE"
fi
