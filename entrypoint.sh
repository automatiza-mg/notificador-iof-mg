#!/bin/bash
set -e

echo "=== Iniciando Notificador IOF MG ==="

# Criar diretório de diários se não existir
mkdir -p /app/diarios
chmod 755 /app/diarios

# Criar diretório instance (onde Flask cria o banco SQLite por padrão)
mkdir -p /app/instance
chmod 755 /app/instance

# Executar migrations Alembic
echo "Executando migrations do banco de dados..."
cd /app
alembic upgrade head

# Verificar se migrations foram executadas com sucesso
if [ $? -eq 0 ]; then
    echo "✓ Migrations executadas com sucesso"
    
    # Fallback: Se migrations não criaram as tabelas, criar manualmente
    echo "Verificando se tabelas foram criadas..."
    python3 << 'EOF'
from app import create_app
from app.extensions import db
from app.utils.db_init import init_db

app = create_app()
with app.app_context():
    try:
        init_db(app)
    except Exception as e:
        print(f"⚠ Aviso ao verificar tabelas: {e}")
EOF
    
    # Verificar se as tabelas foram criadas (debug)
    if [ -f "/app/instance/local.db" ]; then
        echo "✓ Banco de dados criado em /app/instance/local.db"
        # Listar tabelas (se sqlite3 estiver disponível)
        if command -v sqlite3 &> /dev/null; then
            echo "Tabelas no banco:"
            sqlite3 /app/instance/local.db ".tables" || true
        fi
    else
        echo "⚠ Banco de dados não encontrado em /app/instance/local.db"
        echo "Verificando se DATABASE_URL está configurado corretamente..."
    fi
else
    echo "✗ Erro ao executar migrations"
    exit 1
fi

# Iniciar Gunicorn
echo "Iniciando servidor Gunicorn..."
exec gunicorn --config gunicorn_config.py "wsgi:application"
