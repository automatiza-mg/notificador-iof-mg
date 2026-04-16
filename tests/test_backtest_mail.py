"""Testes do helper de envio de email no backtest."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from flask import get_flashed_messages

from app.web.routes import _send_backtest_email


def _build_report() -> Any:
    return SimpleNamespace(
        count=1,
        publish_date=date(2026, 1, 14),
        highlights=[],
        search_terms=[],
    )


def _build_config() -> Any:
    return SimpleNamespace(
        id=1,
        mail_subject="Teste de Busca - Diário Oficial",
        label="Alerta teste",
        mail_to=["destinatario@example.com"],
        attach_csv=False,
    )


def test_send_backtest_email_warns_when_azure_config_missing(app: Any) -> None:
    app.config["MAIL_PROVIDER"] = "azure"
    app.config["AZURE_EMAIL_ENDPOINT"] = (
        "https://automatiza-comms.brazil.communication.azure.com/"
    )
    app.config["AZURE_EMAIL_SENDER_ADDRESS"] = ""
    app.config["AZURE_COMMUNICATION_CONNECTION_STRING"] = (
        "endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=test"
    )

    with app.test_request_context("/"):
        _send_backtest_email(_build_config(), _build_report())
        messages = get_flashed_messages(with_categories=True)

    assert messages == [
        (
            "warning",
            "Configuração Azure Email ausente. Defina AZURE_EMAIL_SENDER_ADDRESS.",
        )
    ]


def test_send_backtest_email_reports_azure_success_message(app: Any) -> None:
    app.config["MAIL_PROVIDER"] = "azure"
    app.config["AZURE_EMAIL_ENDPOINT"] = (
        "https://automatiza-comms.brazil.communication.azure.com/"
    )
    app.config["AZURE_EMAIL_SENDER_ADDRESS"] = "DoNotReply@example.azurecomm.net"
    app.config["AZURE_COMMUNICATION_CONNECTION_STRING"] = (
        "endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=test"
    )

    with app.test_request_context("/"):
        with patch("app.web.routes.build_notification_emails") as build_emails:
            build_emails.return_value = [SimpleNamespace()]
            with patch("app.web.routes.Mailer.send") as send:
                send.return_value = [SimpleNamespace(message_id="msg-123")]
                _send_backtest_email(_build_config(), _build_report())
        messages = get_flashed_messages(with_categories=True)

    assert messages == [
        (
            "success",
            "Email de teste enviado com sucesso para 1 destinatário(s)! "
            "via AZURE (id msg-123)",
        )
    ]
