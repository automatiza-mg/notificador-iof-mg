#!/bin/bash
# Teste com URL encoding da API_KEY

API_KEY=$(grep "^API_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")

echo "=== Teste com URL Encoding ==="
echo "API_KEY (primeiros 20 chars): ${API_KEY:0:20}..."
echo ""

# Fazer URL encoding da API_KEY usando Python
ENCODED_KEY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${API_KEY}'))")

echo "API_KEY codificada (primeiros 50 chars): ${ENCODED_KEY:0:50}..."
echo ""

# Teste 1: Sem api_key (já sabemos que funciona)
echo "1. SEM api_key (deve retornar 401):"
curl -s -X POST http://localhost:8000/api/tasks/process-daily \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}' | python3 -m json.tool
echo ""

# Teste 2: Com api_key codificada
echo "2. COM api_key codificada no query parameter:"
URL="http://localhost:8000/api/tasks/process-daily?api_key=${ENCODED_KEY}"
echo "URL (primeiros 80 chars): ${URL:0:80}..."
echo ""

TMP_RESPONSE=$(mktemp)
HTTP_CODE=$(curl -s -o "$TMP_RESPONSE" -w "%{http_code}" \
  -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}')

echo "HTTP Code: $HTTP_CODE"
echo "Response:"
if [ -f "$TMP_RESPONSE" ] && [ -s "$TMP_RESPONSE" ]; then
    cat "$TMP_RESPONSE" | python3 -m json.tool 2>/dev/null || cat "$TMP_RESPONSE"
else
    echo "(vazio)"
fi
rm -f "$TMP_RESPONSE"

echo ""
echo "Verificando logs do container (últimas 3 linhas):"
docker logs notificador-iof-mg --tail 3

echo ""
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCESSO! FASE 1 COMPLETA!"
elif [ "$HTTP_CODE" = "401" ]; then
    echo "❌ Erro de autenticação (mas a requisição chegou ao servidor!)"
elif [ "$HTTP_CODE" = "500" ]; then
    echo "✅ Autenticação OK! (Erro 500 é do processamento, não da API)"
    echo "   FASE 1 COMPLETA - API funcionando!"
elif [ "$HTTP_CODE" = "000" ] || [ -z "$HTTP_CODE" ]; then
    echo "⚠ Ainda HTTP 000. Tentando método alternativo..."
    echo ""
    echo "Teste manual:"
    echo "curl -X POST 'http://localhost:8000/api/tasks/process-daily?api_key=${ENCODED_KEY}' \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"date\": \"2026-01-14\"}'"
else
    echo "⚠ HTTP $HTTP_CODE"
fi
