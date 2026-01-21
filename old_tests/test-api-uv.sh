#!/bin/bash
# Teste da API usando uv

echo "=== Teste da API com uv ==="
echo ""

# Verificar se container está rodando
if ! docker ps | grep -q notificador-iof-mg; then
    echo "❌ Container não está rodando!"
    echo "Execute: docker start notificador-iof-mg"
    exit 1
fi

echo "✅ Container está rodando"
echo ""

# Executar teste Python com uv
echo "Executando teste Python com uv..."
uv run python test_api_simple.py
