#!/bin/bash
set -e

echo "=== Iniciando Notificador IOF MG ==="

# =========================================================
# Persistência no Azure App Service (Linux Custom Container)
# Em App Service, o diretório persistente é /home quando
# WEBSITES_ENABLE_APP_SERVICE_STORAGE=true.
# =========================================================

DIARIOS_DIR="${DIARIOS_DIR:-/home/diarios}"
INSTANCE_DIR="${INSTANCE_DIR:-/home/instance}"

# Se não vier do App Service, forçamos um default persistente para SQLite
if [ -z "${DATABASE_URL:-}" ]; then
  export DATABASE_URL="sqlite:////home/instance/local.db"
fi

export DIARIOS_DIR INSTANCE_DIR

echo "Usando DIARIOS_DIR=${DIARIOS_DIR}"
echo "Usando INSTANCE_DIR=${INSTANCE_DIR}"
echo "Usando DATABASE_URL=${DATABASE_URL}"

# Criar diretórios persistentes
mkdir -p "${DIARIOS_DIR}" "${INSTANCE_DIR}"
chmod 755 "${DIARIOS_DIR}" "${INSTANCE_DIR}"

# Compatibilidade: cria atalhos para /app/* apontando para /home/*
# (assim qualquer código que use /app/diarios ou /app/instance continua funcionando)
rm -rf /app/diarios /app/instance || true
ln -s "${DIARIOS_DIR}" /app/diarios
ln -s "${INSTANCE_DIR}" /app/instance

# =========================================================
# Migrations
# =========================================================
echo "Executando migrations do banco de dados..."
cd /app
alembic upgrade head

if [ $? -eq 0 ]; then
  echo "✓ Migrations executadas com sucesso"

  # Fallback: garantir tabelas
  echo "Verificando se tabelas foram criadas..."
  python3 << 'EOF'
from app import create_app
from app.utils.db_init import init_db

app = create_app()
with app.app_context():
    try:
        init_db(app)
    except Exception as e:
        print(f"⚠ Aviso ao verificar/criar tabelas: {e}")
EOF

  # Descobrir o caminho do DB se for SQLite
  DB_PATH=""
  if [[ "${DATABASE_URL}" == sqlite:////* ]]; then
    DB_PATH="/${DATABASE_URL#sqlite:////}"
  fi

  if [ -n "${DB_PATH}" ] && [ -f "${DB_PATH}" ]; then
    echo "✓ Banco de dados encontrado em ${DB_PATH}"
  else
    echo "⚠ Banco de dados SQLite não encontrado ainda (isso pode ser normal no primeiro start)."
    echo "  DATABASE_URL=${DATABASE_URL}"
  fi

else
  echo "✗ Erro ao executar migrations"
  exit 1
fi

# =========================================================
# Iniciar Gunicorn
# =========================================================
echo "Iniciando servidor Gunicorn..."
exec gunicorn --config gunicorn_config.py "wsgi:application"
