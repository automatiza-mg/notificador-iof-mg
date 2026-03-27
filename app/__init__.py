"""Factory pattern para criação da aplicação Flask."""

import os
from typing import TYPE_CHECKING, Any

from dotenv import load_dotenv
from flask import Flask, redirect, request, url_for

from app.api import features, search_config, tasks
from app.cli import register_commands
from app.config import config_by_name
from app.extensions import db, login_manager, mail
from app.models import User
from app.utils.errors import unauthorized as api_unauthorized
from app.web import routes as web_routes

# Carregar variáveis de ambiente
load_dotenv()


def create_app(config_name: str | None = None) -> Flask:
    """
    Factory function para criar e configurar a aplicação Flask.

    Args:
        config_name: Nome da configuração ('development', 'production', etc.)
                    Se None, usa APP_ENV da variável de ambiente.

    Returns:
        Instância configurada da aplicação Flask.
    """
    app = Flask(__name__)

    # Importar configuração
    # Determinar ambiente
    env_name = str(config_name or os.getenv("APP_ENV", "development"))
    app.config.from_object(config_by_name[env_name])

    # Inicializar extensões
    db.init_app(app)
    if app.config.get("MAIL_PROVIDER") == "smtp":
        mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "web.login"
    login_manager.session_protection = "basic"

    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id)) if user_id else None

    # Registrar loader sem usar decorador para evitar erro de untyped-decorator no Mypy
    login_manager.user_loader(load_user)

    def unauthorized() -> Any:
        if request.path.startswith("/api/"):
            return api_unauthorized()
        return redirect(url_for("web.login", next=request.url))

    login_manager.unauthorized_handler(unauthorized)

    # Registrar blueprints
    app.register_blueprint(search_config.bp)
    app.register_blueprint(features.bp)
    app.register_blueprint(tasks.bp)

    # Registrar blueprint web (HTML)
    app.register_blueprint(web_routes.bp)

    # Registrar comandos CLI (create-user, seed-test-users)
    register_commands(app)

    return app
