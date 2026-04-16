"""Testes de descadastro por link assinado."""

from __future__ import annotations

import time
from datetime import date
from typing import Any

import pytest
from itsdangerous import BadSignature, SignatureExpired

from app.mailer.notification import build_notification_emails, notification_email
from app.mailer.unsubscribe import (
    build_unsubscribe_url,
    generate_unsubscribe_token,
    load_unsubscribe_token,
    normalize_email,
    resolve_app_base_url,
)
from app.models import SearchConfig
from app.repositories.search_config_repository import SearchConfigRepository
from app.search.source import Highlight, Report, Term, Trigger
from app.services.search_service import SearchService

TEST_SECRET_KEY = str(object())
TEST_TOKEN_VALUE = str(123456)


def _build_report() -> Report:
    return Report(
        publish_date=date(2026, 1, 14),
        highlights=[
            Highlight(
                page=5,
                content="Trecho relevante do diario oficial.",
                term="licitacao",
                page_url="https://example.com/page/5",
            )
        ],
        search_terms=[Term(term="licitacao", exact=True)],
        trigger=Trigger.CRON,
        count=1,
    )


def test_generate_and_load_unsubscribe_token() -> None:
    token = generate_unsubscribe_token(
        config_id=10,
        email="User@Example.com ",
        secret_key=TEST_SECRET_KEY,
    )

    payload = load_unsubscribe_token(
        token=token,
        secret_key=TEST_SECRET_KEY,
        max_age_seconds=60,
    )

    assert payload.config_id == 10
    assert payload.email == "user@example.com"


def test_load_unsubscribe_token_rejects_invalid_signature() -> None:
    token = generate_unsubscribe_token(
        config_id=1,
        email="user@example.com",
        secret_key=TEST_SECRET_KEY,
    )

    with pytest.raises(BadSignature):
        load_unsubscribe_token(
            token=f"{token}tampered",
            secret_key=TEST_SECRET_KEY,
            max_age_seconds=60,
        )


def test_load_unsubscribe_token_rejects_expired() -> None:
    token = generate_unsubscribe_token(
        config_id=1,
        email="user@example.com",
        secret_key=TEST_SECRET_KEY,
    )

    time.sleep(1)

    with pytest.raises(SignatureExpired):
        load_unsubscribe_token(
            token=token,
            secret_key=TEST_SECRET_KEY,
            max_age_seconds=0,
        )


def test_resolve_app_base_url_in_dev_and_prod() -> None:
    assert (
        resolve_app_base_url(configured_base_url="", app_env="development")
        == "http://localhost:5000"
    )
    assert (
        resolve_app_base_url(
            configured_base_url="https://app.example.com/",
            app_env="production",
        )
        == "https://app.example.com"
    )

    with pytest.raises(RuntimeError, match="APP_BASE_URL"):
        resolve_app_base_url(configured_base_url="", app_env="production")


def test_build_unsubscribe_url_contains_token() -> None:
    url = build_unsubscribe_url(
        app_base_url="https://app.example.com",
        token=TEST_TOKEN_VALUE,
    )

    assert url == f"https://app.example.com/unsubscribe?token={TEST_TOKEN_VALUE}"


def test_unsubscribe_service_removes_email_without_deactivating(
    app: Any, sample_config: Any
) -> None:
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)
        config = repo.get_by_id(sample_config.id)
        assert config is not None
        config.mail_to = ["first@example.com", "second@example.com"]
        repo.save(config)

        result = service.unsubscribe_email_from_config(
            sample_config.id,
            "SECOND@example.com",
        )

        assert result.status == "removed"
        assert result.deactivated is False
        assert result.config is not None
        assert result.config.mail_to == ["first@example.com"]
        assert result.config.active is True


def test_unsubscribe_service_deactivates_when_last_email_removed(
    app: Any, sample_config: Any
) -> None:
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        result = service.unsubscribe_email_from_config(
            sample_config.id,
            "test@example.com",
        )

        assert result.status == "removed"
        assert result.deactivated is True
        assert result.config is not None
        assert result.config.mail_to == []
        assert result.config.active is False


def test_unsubscribe_service_is_idempotent(app: Any, sample_config: Any) -> None:
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        service.unsubscribe_email_from_config(sample_config.id, "test@example.com")
        result = service.unsubscribe_email_from_config(
            sample_config.id, "test@example.com"
        )

        assert result.status == "already_removed"
        assert result.config is not None
        assert result.config.active is False


def test_notification_email_includes_unsubscribe_link() -> None:
    email = notification_email(
        ["destinatario@example.com"],
        _build_report(),
        alert_label="Alerta Licitacao",
        unsubscribe_url="https://app.example.com/unsubscribe?token=abc",
    )

    assert "Descadastre este email" in email.text
    assert "https://app.example.com/unsubscribe?token=abc" in email.text
    assert email.html is not None
    assert "Descadastrar e-mail" in email.html


def test_build_notification_emails_creates_one_message_per_recipient(
    app: Any, sample_config: Any
) -> None:
    with app.app_context():
        config = SearchConfig.query.filter_by(id=sample_config.id).first()
        assert config is not None
        config.mail_to = ["one@example.com", "two@example.com"]

        emails = build_notification_emails(
            config=config,
            report=_build_report(),
            secret_key=str(app.config["SECRET_KEY"]),
            app_base_url="",
            app_env="testing",
        )

    assert len(emails) == 2
    assert emails[0].to == ["one@example.com"]
    assert emails[1].to == ["two@example.com"]
    assert emails[0].html is not None
    assert emails[1].html is not None
    assert "token=" in emails[0].html
    assert "token=" in emails[1].html


def test_unsubscribe_route_success(app: Any, client: Any, sample_config: Any) -> None:
    token = generate_unsubscribe_token(
        config_id=sample_config.id,
        email="test@example.com",
        secret_key=str(app.config["SECRET_KEY"]),
    )

    response = client.get(f"/unsubscribe?token={token}")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Descadastro concluído" in html
    assert "foi descadastrado com sucesso" in html

    with app.app_context():
        config = SearchConfig.query.filter_by(id=sample_config.id).first()
        assert config is not None
        assert config.mail_to == []
        assert config.active is False


def test_unsubscribe_route_invalid_token(client: Any) -> None:
    response = client.get("/unsubscribe?token=token-invalido")

    assert response.status_code == 200
    assert "Link inválido" in response.get_data(as_text=True)


def test_unsubscribe_route_already_removed(
    app: Any, client: Any, sample_config: Any
) -> None:
    token = generate_unsubscribe_token(
        config_id=sample_config.id,
        email="test@example.com",
        secret_key=str(app.config["SECRET_KEY"]),
    )

    client.get(f"/unsubscribe?token={token}")
    response = client.get(f"/unsubscribe?token={token}")

    assert response.status_code == 200
    assert "Email já descadastrado" in response.get_data(as_text=True)


def test_normalize_email() -> None:
    assert normalize_email("  USER@Example.com ") == "user@example.com"
