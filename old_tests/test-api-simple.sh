#!/bin/bash
# Teste simples da API

echo "=== Teste Simples da API ==="
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

echo "1. Testando sem API_KEY (deve retornar 401):"
curl -s -w "\nHTTP: %{http_code}\n" -X POST http://localhost:8000/api/tasks/process-daily \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}'
echo ""

echo "2. Testando com API_KEY incorreta (deve retornar 401):"
curl -s -w "\nHTTP: %{http_code}\n" -X POST http://localhost:8000/api/tasks/process-daily \
  -H "X-API-Key: wrong-key" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}'
echo ""

echo "3. Testando com API_KEY correta mas data inválida (deve retornar 400):"
curl -s -w "\nHTTP: %{http_code}\n" -X POST http://localhost:8000/api/tasks/process-daily \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"date": "data-invalida"}'
echo ""

echo "4. Testando com API_KEY correta e data válida (deve retornar 200 ou 500 se houver erro no processamento):"
RESPONSE4=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:8000/api/tasks/process-daily \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}')
HTTP_CODE4=$(echo "$RESPONSE4" | grep "HTTP_CODE:" | cut -d: -f2)
BODY4=$(echo "$RESPONSE4" | grep -v "HTTP_CODE:")
echo "HTTP: $HTTP_CODE4"
echo "$BODY4" | python3 -m json.tool 2>/dev/null || echo "$BODY4"
echo ""

echo "5. Testando sem data (deve usar data de hoje):"
RESPONSE5=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:8000/api/tasks/process-daily \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}')
HTTP_CODE5=$(echo "$RESPONSE5" | grep "HTTP_CODE:" | cut -d: -f2)
BODY5=$(echo "$RESPONSE5" | grep -v "HTTP_CODE:")
echo "HTTP: $HTTP_CODE5"
echo "$BODY5" | python3 -m json.tool 2>/dev/null || echo "$BODY5"
echo ""
