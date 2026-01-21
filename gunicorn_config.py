"""Configuração do Gunicorn para produção."""
import os
import multiprocessing

# Bind address e porta
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Workers
# Fórmula: (2 x CPU cores) + 1
# Para Azure, geralmente 2-4 workers é suficiente
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
# Limitar a 4 workers para não sobrecarregar
if workers > 4:
    workers = 4

# Worker class
worker_class = "sync"

# Timeout (importante para processamento de PDFs que pode demorar)
timeout = int(os.getenv('GUNICORN_TIMEOUT', '300'))  # 5 minutos

# Keepalive
keepalive = 5

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# Process naming
proc_name = "notificador-iof-mg"

# Worker temp directory
worker_tmp_dir = "/dev/shm"  # Usar shared memory se disponível

# Preload app (melhora performance, mas pode causar problemas com workers)
preload_app = False

# Max requests (restart worker após N requests para evitar memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Graceful timeout
graceful_timeout = 30
