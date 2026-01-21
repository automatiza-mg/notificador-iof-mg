"""WSGI entry point para Gunicorn."""
from app import create_app
import os

# Criar aplicação Flask
# Gunicorn vai usar esta variável 'application'
application = create_app(config_name=os.getenv('APP_ENV', 'production'))
