"""Extensões Flask (SQLAlchemy, Mail, LoginManager, etc.)."""
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager

# Inicializar extensões
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()

