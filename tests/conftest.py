"""Configuração de testes e fixtures."""

import os
from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from app import create_app
from app.extensions import db
from app.models import User
from app.models.search_config import SearchConfig


@pytest.fixture
def app() -> Generator[Flask]:
    """Cria uma aplicação configurada para testes."""
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    flask_app = create_app()

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Client de teste do Flask."""
    return app.test_client()


@pytest.fixture
def test_user(app: Flask) -> User:
    """Usuário de teste (email/senha conhecidos para login)."""
    with app.app_context():
        user = User(
            email="testuser@example.com",
            auth_provider="local",
        )
        user.set_password("testpass123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def test_user_b(app: Flask) -> User:
    """Segundo usuário para testes multi-tenant."""
    with app.app_context():
        user = User(
            email="userb@example.com",
            auth_provider="local",
        )
        user.set_password("passb123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def client_logged_in(app: Flask, client: FlaskClient, test_user: User) -> FlaskClient:
    """Client com sessão autenticada (test_user) via sessão Flask-Login."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(test_user.id)
    return client


@pytest.fixture
def sample_config(app: Flask, test_user: User) -> SearchConfig:
    """Configuração de exemplo no banco (pertence a test_user)."""
    with app.app_context():
        config = SearchConfig(
            user_id=test_user.id,
            label="Test Config",
            description="Config for testing",
            attach_csv=False,
            mail_to=["test@example.com"],
            mail_subject="Test Subject",
            active=True,
        )
        db.session.add(config)
        db.session.commit()
        db.session.refresh(config)
        return config


@pytest.fixture
def runner(app: Flask) -> FlaskCliRunner:
    """Test runner do Flask."""
    return app.test_cli_runner()
