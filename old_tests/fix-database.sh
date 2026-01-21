#!/bin/bash
# Script para corrigir o banco de dados no container

echo "=== Corrigindo Banco de Dados ==="

# Verificar se container está rodando
if ! docker ps | grep -q "notificador-iof-mg"; then
    echo "❌ Container não está rodando. Execute: docker start notificador-iof-mg"
    exit 1
fi

echo "1. Verificando diretórios..."
docker exec notificador-iof-mg mkdir -p /app/instance
docker exec notificador-iof-mg mkdir -p /app/diarios

echo "2. Executando migrations novamente..."
docker exec notificador-iof-mg alembic upgrade head

echo "3. Verificando se banco existe..."
docker exec notificador-iof-mg ls -la /app/instance/ || echo "Diretório instance não encontrado"

echo "4. Verificando tabelas (se sqlite3 estiver disponível)..."
docker exec notificador-iof-mg sh -c "if command -v sqlite3 &> /dev/null; then sqlite3 /app/instance/local.db '.tables' 2>/dev/null || echo 'Banco não encontrado ou sqlite3 não disponível'; fi"

echo ""
echo "5. Reiniciando container..."
docker restart notificador-iof-mg

echo ""
echo "✓ Correção aplicada! Verifique os logs:"
echo "  docker logs -f notificador-iof-mg"
