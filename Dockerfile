# Dockerfile para Notificador IOF MG
# Base: Python 3.13 slim
FROM python:3.13-slim

# Metadados
LABEL maintainer="notificador-iof-mg"
LABEL description="Sistema de notificações do Diário Oficial de Minas Gerais"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema (poppler-utils)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Instalar UV (gerenciador de pacotes Python moderno)
RUN pip install --no-cache-dir uv

# Criar diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências primeiro (para cache do Docker)
COPY pyproject.toml ./

# Instalar dependências Python usando UV
# UV pode instalar diretamente do pyproject.toml usando pip install
# Primeiro instalamos as dependências, depois o projeto em modo editável
RUN uv pip install --system \
    flask>=3.0.0 \
    flask-sqlalchemy>=3.1.0 \
    flask-mail>=0.9.1 \
    sqlalchemy>=2.0.0 \
    alembic>=1.13.0 \
    psycopg[binary]>=3.1.0 \
    python-dotenv>=1.0.0 \
    pydantic>=2.0.0 \
    requests>=2.31.0 \
    redis>=5.0.0 \
    rq>=1.15.0 \
    gunicorn>=21.2.0

# Copiar código da aplicação (necessário para instalar módulos locais)
COPY . .

# Instalar o projeto em modo editável (para que os módulos locais sejam importáveis)
RUN uv pip install --system -e .

# Criar diretório para diários (será montado como volume na Azure)
RUN mkdir -p /app/diarios && chmod 755 /app/diarios

# Tornar entrypoint executável
RUN chmod +x entrypoint.sh

# Expor porta (Azure usa 8000 por padrão, mas aceita PORT env var)
EXPOSE 8000

# Health check (usando curl que será instalado se necessário, ou Python simples)
# Azure Web App tem seu próprio health check, então este é opcional
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/features')" || exit 1

# Entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Comando padrão (será sobrescrito pelo entrypoint)
CMD ["gunicorn", "--config", "gunicorn_config.py", "wsgi:application"]
