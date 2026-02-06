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
    API_KEY = os.getenv('API_KEY', '')  # Para proteger rotas administrativas
    
    # Banco de Dados
    # Por padrão, Flask cria SQLite em instance/ quando usa sqlite:///
    # Garantir que o caminho seja absoluto e explícito
    _database_url = os.getenv('DATABASE_URL', '')
    if not _database_url or _database_url == 'sqlite:///local.db':
        # Calcular caminho absoluto para instance/local.db
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        instance_dir = os.path.join(base_dir, 'instance')
        # Criar diretório se não existir (fazer de forma segura)
        try:
            os.makedirs(instance_dir, exist_ok=True)
        except (OSError, PermissionError):
            pass  # Se falhar, Flask tentará criar
        default_db_path = os.path.join(instance_dir, 'local.db')
        _database_url = f'sqlite:///{default_db_path}'
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # IOF
    IOF_USERNAME = os.getenv('IOF_USERNAME', '')
    IOF_PASSWORD = os.getenv('IOF_PASSWORD', '')
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SMTP_HOST', '')
    MAIL_PORT = int(os.getenv('MAIL_SMTP_PORT', '587'))
    # Para Gmail na porta 587, TLS é obrigatório
    # Se MAIL_USE_TLS não estiver definido, inferir baseado na porta
    mail_port_str = os.getenv('MAIL_SMTP_PORT', '587')
    mail_host = os.getenv('MAIL_SMTP_HOST', '').lower()
    
    # Gmail sempre requer TLS na porta 587
    if 'gmail' in mail_host and mail_port_str == '587':
        default_use_tls = True
    elif mail_port_str in ('587', '25'):
        default_use_tls = True
    elif mail_port_str == '465':
        default_use_tls = False  # Porta 465 usa SSL, não TLS
    else:
        default_use_tls = False
    
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', '').lower()
    if MAIL_USE_TLS == '':
        MAIL_USE_TLS = default_use_tls
    else:
        MAIL_USE_TLS = MAIL_USE_TLS == 'true'
    
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_SMTP_USER', '')
    MAIL_PASSWORD = os.getenv('MAIL_SMTP_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_FROM_ADDRESS', 'noreply@example.com')
    
    # Redis (para RQ)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Microsoft Entra ID (SSO)
    ENTRA_TENANT_ID = os.getenv('ENTRA_TENANT_ID', '')
    ENTRA_CLIENT_ID = os.getenv('ENTRA_CLIENT_ID', '')
    ENTRA_CLIENT_SECRET = os.getenv('ENTRA_CLIENT_SECRET', '')
    _entra_authority = os.getenv('ENTRA_AUTHORITY', '')
    if not _entra_authority and os.getenv('ENTRA_TENANT_ID'):
        _entra_authority = f"https://login.microsoftonline.com/{os.getenv('ENTRA_TENANT_ID')}"
    ENTRA_AUTHORITY = _entra_authority
    ENTRA_REDIRECT_URI = os.getenv('ENTRA_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    ENTRA_SCOPES = os.getenv('ENTRA_SCOPES', 'openid profile email')


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

