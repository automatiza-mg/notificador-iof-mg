"""Configuração de testes e fixtures."""

import os
import pytest
from app import create_app
from app.extensions import db
from app.models.search_config import SearchConfig


@pytest.fixture
def app():
    """Cria uma aplicação configurada para testes."""
    # Configurar ambiente para testes
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    app = create_app()

    # Criar tabelas
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Client de teste do Flask."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test runner do Flask."""
    return app.test_cli_runner()


@pytest.fixture
def sample_config(app):
    """Cria uma configuração de exemplo no banco."""
    config = SearchConfig(
        label="Test Config",
        description="Config for testing",
        attach_csv=False,
        mail_to=["test@example.com"],
        mail_subject="Test Subject",
        active=True,
    )
    with app.app_context():
        db.session.add(config)
        db.session.commit()
        # Refresh para ter o ID
        db.session.refresh(config)
        return config
