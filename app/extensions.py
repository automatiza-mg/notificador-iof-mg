"""Extensões Flask (SQLAlchemy, Mail, LoginManager, etc.)."""

from typing import Any

import flask_login
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

LoginManager: Any = getattr(flask_login, "LoginManager")  # noqa: B009

# Inicializar extensões
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
