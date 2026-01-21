#!/bin/bash
# Teste simples e direto

# Obter API_KEY
API_KEY=$(grep "^API_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")

echo "Testando POST com api_key no query parameter..."
echo "API_KEY: ${API_KEY:0:15}..."
echo ""

# Teste direto
curl -v -X POST "http://localhost:8000/api/tasks/process-daily?api_key=${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}' 2>&1 | head -40
