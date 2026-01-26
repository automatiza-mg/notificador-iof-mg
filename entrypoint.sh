
#!/usr/bin/env bash
set -Eeuo pipefail

log() { echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*"; }

mask_url() {
  # Best-effort: hide credentials in URLs like scheme://user:pass@host/...
  local url="$1"
  if [[ "$url" == *"://"*"@"* ]]; then
    local prefix="${url%%://*}://"
    local rest="${url#*://}"
    local after_at="${rest#*@}"
    echo "${prefix}***:***@${after_at}"
  else
    echo "(definida)"
  fi
}

log "=== Iniciando Notificador IOF MG ==="

DIARIOS_DIR="${DIARIOS_DIR:-/home/diarios}"
INSTANCE_DIR="${INSTANCE_DIR:-/home/instance}"

if [[ -z "${DATABASE_URL:-}" ]]; then
  export DATABASE_URL="sqlite:////home/instance/local.db"
fi

export DIARIOS_DIR INSTANCE_DIR

log "Usando DIARIOS_DIR=${DIARIOS_DIR}"
log "Usando INSTANCE_DIR=${INSTANCE_DIR}"
log "Usando DATABASE_URL=$(mask_url "${DATABASE_URL}")"

mkdir -p "${DIARIOS_DIR}" "${INSTANCE_DIR}"
chmod 755 "${DIARIOS_DIR}" "${INSTANCE_DIR}" || true

rm -rf /app/diarios /app/instance || true
ln -s "${DIARIOS_DIR}" /app/diarios
ln -s "${INSTANCE_DIR}" /app/instance

log "Executando migrations do banco de dados..."
cd /app

if alembic upgrade head; then
  log "✓ Migrations executadas com sucesso"
else
  log "✗ Erro ao executar migrations"
  exit 1
fi

log "Verificando se tabelas foram criadas..."
python3 << 'PY'
from app import create_app
from app.utils.db_init import init_db

app = create_app()
with app.app_context():
    try:
        init_db(app)
        print("[db_init] OK")
    except Exception as e:
        print(f"[db_init] Aviso ao verificar/criar tabelas: {e}")
PY

if [[ "${DATABASE_URL}" == sqlite:////* ]]; then
  db_path="/${DATABASE_URL#sqlite:////}"
  if [[ -f "${db_path}" ]]; then
    log "✓ Banco de dados SQLite encontrado em ${db_path}"
  else
    log "⚠ Banco de dados SQLite não encontrado ainda (isso pode ser normal no primeiro start)"
  fi
else
  log "✓ Banco configurado via DATABASE_URL (não-SQLite)"
fi

log "Iniciando servidor Gunicorn..."
exec gunicorn --config gunicorn_config.py "wsgi:application"
