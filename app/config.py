"""Configurações da aplicação."""
import os
from typing import Dict, Type


class Config:
    """Configuração base."""
    
    # Aplicação
    APP_NAME = os.getenv('APP_NAME', 'notificador-iof-mg')
    APP_ENV = os.getenv('APP_ENV', 'development')
    CLIENT_URL = os.getenv('CLIENT_URL', 'http://localhost:5173')
    DIARIOS_DIR = os.getenv('DIARIOS_DIR', 'diarios')
    
    # Segurança
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Banco de Dados
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///local.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # IOF
    IOF_USERNAME = os.getenv('IOF_USERNAME', '')
    IOF_PASSWORD = os.getenv('IOF_PASSWORD', '')
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SMTP_HOST', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_SMTP_PORT', '1025'))
    MAIL_USE_TLS = os.getenv('MAIL_SMTP_PORT', '1025') != '1025'
    MAIL_USERNAME = os.getenv('MAIL_SMTP_USER', '')
    MAIL_PASSWORD = os.getenv('MAIL_SMTP_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_FROM_ADDRESS', 'noreply@example.com')
    
    # Redis (para RQ)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')


class DevelopmentConfig(Config):
    """Configuração para desenvolvimento."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuração para produção."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configuração para testes."""
    DEBUG = True
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'


# Mapeamento de nomes de configuração para classes
config_by_name: Dict[str, Type[Config]] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}

