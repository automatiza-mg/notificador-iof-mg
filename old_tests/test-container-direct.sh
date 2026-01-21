#!/bin/bash
# Teste direto dentro do container

API_KEY=$(grep "^API_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")

echo "=== Teste Direto no Container ==="
echo ""

# Teste 1: Verificar se a API_KEY está no container
echo "1. Verificando API_KEY no container:"
docker exec notificador-iof-mg env | grep API_KEY | head -1
echo ""

# Teste 2: Testar a rota diretamente dentro do container usando curl
echo "2. Testando rota dentro do container (sem query parameter primeiro):"
docker exec notificador-iof-mg curl -s -X POST http://localhost:8000/api/tasks/process-daily \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-01-14"}' | python3 -m json.tool 2>/dev/null || echo "Erro ao executar no container"
echo ""

# Teste 3: Testar com api_key no query parameter dentro do container
echo "3. Testando com api_key no query parameter (dentro do container):"
docker exec notificador-iof-mg sh -c "curl -s -X POST 'http://localhost:8000/api/tasks/process-daily?api_key=${API_KEY}' -H 'Content-Type: application/json' -d '{\"date\": \"2026-01-14\"}'" | python3 -m json.tool 2>/dev/null || echo "Erro"
echo ""

# Teste 4: Testar usando Python dentro do container
echo "4. Testando usando Python dentro do container:"
docker exec notificador-iof-mg python3 -c "
import os
import urllib.request
import json

api_key = os.getenv('API_KEY')
url = f'http://localhost:8000/api/tasks/process-daily?api_key={api_key}'
data = json.dumps({'date': '2026-01-14'}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
req.get_method = lambda: 'POST'

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f'HTTP {response.getcode()}: {response.read().decode()[:200]}')
except Exception as e:
    print(f'Erro: {e}')
"
