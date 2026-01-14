"""Extensões Flask (SQLAlchemy, Mail, etc.)."""
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# Inicializar extensões
db = SQLAlchemy()
mail = Mail()

