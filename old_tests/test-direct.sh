#!/bin/bash
# Teste direto sem scripts complexos

API_KEY=$(grep "^API_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")

echo "Testando POST direto com curl verbose..."
echo "API_KEY (primeiros 20 chars): ${API_KEY:0:20}..."
echo ""

# Teste 1: Sem api_key (deve dar 401)
echo "=== Teste 1: SEM api_key ==="
curl -X POST http://localhost:8000/api/tasks/process-daily \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}' \
  -w "\nHTTP: %{http_code}\n" \
  -s
echo ""

# Teste 2: Com api_key no query (URL encoding)
echo "=== Teste 2: COM api_key no query (sem encoding) ==="
curl -X POST "http://localhost:8000/api/tasks/process-daily?api_key=${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}' \
  -w "\nHTTP: %{http_code}\n" \
  -v 2>&1 | grep -E "(HTTP|error|success|date)" | head -10
echo ""

# Teste 3: Verificar logs do container
echo "=== Últimos logs do container ==="
docker logs notificador-iof-mg --tail 5
