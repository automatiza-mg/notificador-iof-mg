#!/usr/bin/env python3
"""Teste simples da API usando requests."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
BASE_URL = 'http://localhost:8000'

print("=== Teste Simples da API ===")
print(f"API_KEY (primeiros 20 chars): {API_KEY[:20] if API_KEY else 'NÃO ENCONTRADA'}...")
print()

# Teste 1: Sem api_key
print("1. Testando SEM api_key (deve retornar 401):")
try:
    response = requests.post(
        f'{BASE_URL}/api/tasks/process-daily',
        json={'date': '2026-01-14'},
        timeout=10
    )
    print(f"   HTTP {response.status_code}: {response.text[:100]}")
except Exception as e:
    print(f"   ERRO: {e}")
print()

# Teste 2: Com api_key no query parameter
print("2. Testando COM api_key no query parameter:")
try:
    response = requests.post(
        f'{BASE_URL}/api/tasks/process-daily?api_key={API_KEY}',
        json={'date': '2026-01-14'},
        timeout=30  # Timeout maior para processamento
    )
    print(f"   HTTP {response.status_code}")
    print(f"   Response: {response.text[:200]}")
    
    if response.status_code == 200:
        print("   ✅ SUCESSO!")
    elif response.status_code == 401:
        print("   ❌ Erro de autenticação")
    elif response.status_code == 500:
        print("   ⚠ Erro 500 (pode ser normal se houver erro no processamento)")
        print("   ✅ Mas a autenticação funcionou!")
except requests.exceptions.Timeout:
    print("   ⚠ Timeout (o processamento pode estar demorando)")
except Exception as e:
    print(f"   ❌ ERRO: {e}")
print()

# Teste 3: Verificar se a rota existe
print("3. Testando /api/features (deve funcionar):")
try:
    response = requests.get(f'{BASE_URL}/api/features', timeout=5)
    print(f"   HTTP {response.status_code}: {response.json()}")
except Exception as e:
    print(f"   ERRO: {e}")
