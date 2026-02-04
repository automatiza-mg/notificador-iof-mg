"""Factory pattern para criação da aplicação Flask."""
from flask import Flask
from dotenv import load_dotenv

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
    from app.config import config_by_name
    
    # Determinar ambiente
    import os
    env = config_name or os.getenv('APP_ENV', 'development')
    app.config.from_object(config_by_name[env])
    
    # Inicializar extensões
    from app.extensions import db, mail, login_manager
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "web.login"
    login_manager.session_protection = "basic"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id)) if user_id else None

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request
        if request.path.startswith("/api/"):
            from app.utils.errors import unauthorized as api_unauthorized
            return api_unauthorized()
        from flask import redirect, url_for
        return redirect(url_for("web.login", next=request.url))
    # Registrar blueprints
    from app.api import search_config, features, tasks
    app.register_blueprint(search_config.bp)
    app.register_blueprint(features.bp)
    app.register_blueprint(tasks.bp)
    
    # Registrar blueprint web (HTML)
    from app.web import routes as web_routes
    app.register_blueprint(web_routes.bp)

    # Registrar comandos CLI (create-user, seed-test-users)
    from app.cli import register_commands
    register_commands(app)
    
    return app

