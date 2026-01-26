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

# NÃO vazar credenciais no log: mascarar user:pass@
# Ex.: postgresql+psycopg://user:pass@host/db  -> postgresql+psycopg://***:***@host/db
if echo "$DATABASE_URL" | grep -q '://'; then
  MASKED_DATABASE_URL="${DATABASE_URL}"
  # só mascara se tiver '@' depois do esquema
  case "$DATABASE_URL" in
    *://*@*)
      scheme="${DATABASE_URL%%://*}://"
      rest="${DATABASE_URL#*://}"
      after_at="${rest#*@}"
      MASKED_DATABASE_URL="${scheme}***:***@${after_at}"
      ;;
  esac
  echo "Usando DATABASE_URL=${MASKED_DATABASE_URL}"
else
  echo "Usando DATABASE_URL=(definida)"
fi

# Criar diretórios persistentes
mkdir -p "${DIARIOS_DIR}" "${INSTANCE_DIR}"
chmod 755 "${DIARIOS_DIR}" "${INSTANCE_DIR}" || true

# Compatibilidade: cria atalhos para /app/* apontando para /home/*
rm -rf /app/diarios /app/instance || true
ln -s "${DIARIOS_DIR}" /app/diarios
ln -s "${INSTANCE_DIR}" /app/instance

# =========================================================
# Migrations
# =========================================================
echo "Executando migrations do banco de dados..."
cd /app
alembic upgrade head

echo "Migrations executadas. Verificando/criando tabelas (idempotente)..."
python3 << 'PY'
from app import create_app
from app.utils.db_init import init_db

app = create_app()
with app.app_context():
    try:
        init_db(app)
        print('[db_init] OK')
    except Exception as e:
        print(f'[db_init] Aviso: {e}')
PY

# Diagnóstico: se for SQLite, verificar arquivo; se for Postgres, não há arquivo local.
if [[ "${DATABASE_URL}" == sqlite:////* ]]; then
  DB_PATH="/${DATABASE_URL#sqlite:////}"
  if [ -f "${DB_PATH}" ]; then
    echo "Banco SQLite encontrado em ${DB_PATH}"
  else
    echo "Banco SQLite ainda nao encontrado (normal no primeiro start)."
  fi
else
  echo "Banco configurado via DATABASE_URL (nao-SQLite)."
fi

# =========================================================
# Iniciar Gunicorn
# =========================================================
echo "Iniciando servidor Gunicorn..."
exec gunicorn --config gunicorn_config.py "wsgi:application"
