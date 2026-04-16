"""Testes para providers e fachada de email."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.mailer.mailer import Mailer
from app.mailer.message import Attachment, Email
from app.mailer.notification import build_notification_emails, notification_email
from app.models.search_config import SearchConfig
from app.search.source import Highlight, Report, Term, Trigger


def _build_report() -> Report:
    return Report(
        publish_date=date(2026, 1, 14),
        highlights=[
            Highlight(
                page=3,
                content="Trecho de teste",
                term="licitacao",
                page_url="https://example.com/page/3",
            )
        ],
        search_terms=[Term(term="licitacao", exact=True)],
        trigger=Trigger.CRON,
        count=1,
    )


def test_mailer_uses_azure_by_default_in_production() -> None:
    app = SimpleNamespace(
        config={
            "MAIL_PROVIDER": "azure",
            "AZURE_EMAIL_ENDPOINT": "https://automatiza-comms.brazil.communication.azure.com/",
            "AZURE_EMAIL_SENDER_ADDRESS": "DoNotReply@example.azurecomm.net",
            "AZURE_COMMUNICATION_CONNECTION_STRING": "endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=test",
        }
    )

    mailer = Mailer(app)

    assert mailer.provider_name == "azure"
    assert mailer.validate_configuration() is None


def test_mailer_uses_smtp_in_development() -> None:
    app = SimpleNamespace(
        config={
            "MAIL_PROVIDER": "smtp",
            "MAIL_SERVER": "localhost",
            "MAIL_PORT": 1025,
        }
    )

    mailer = Mailer(app)

    assert mailer.provider_name == "smtp"
    assert mailer.validate_configuration() is None


def test_mailer_validate_configuration_for_azure_missing_sender() -> None:
    app = SimpleNamespace(
        config={
            "MAIL_PROVIDER": "azure",
            "AZURE_EMAIL_ENDPOINT": "https://automatiza-comms.brazil.communication.azure.com/",
            "AZURE_EMAIL_SENDER_ADDRESS": "",
            "AZURE_COMMUNICATION_CONNECTION_STRING": "endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=test",
        }
    )

    mailer = Mailer(app)

    assert mailer.validate_configuration() == (
        "Configuração Azure Email ausente. Defina AZURE_EMAIL_SENDER_ADDRESS."
    )


def test_azure_provider_serializes_html_and_attachments() -> None:
    app = SimpleNamespace(
        config={
            "MAIL_PROVIDER": "azure",
            "AZURE_EMAIL_ENDPOINT": "https://automatiza-comms.brazil.communication.azure.com/",
            "AZURE_EMAIL_SENDER_ADDRESS": "DoNotReply@example.azurecomm.net",
            "AZURE_COMMUNICATION_CONNECTION_STRING": "endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=test",
        }
    )
    mailer = Mailer(app)
    azure_client = MagicMock()
    azure_result = SimpleNamespace(message_id="message-123")
    azure_client.begin_send.return_value.result.return_value = azure_result
    fake_email_module = SimpleNamespace(
        EmailClient=SimpleNamespace(
            from_connection_string=MagicMock(return_value=azure_client)
        )
    )
    email = Email(
        to=["destinatario@example.com"],
        subject="Assunto",
        text="Corpo texto",
        html="<p>Corpo html</p>",
        attachments=[
            Attachment(filename="arquivo.csv", content=b"abc", content_type="text/csv")
        ],
    )

    with patch(
        "app.mailer.azure_provider.import_module", return_value=fake_email_module
    ):
        results = mailer.send(email)

    assert results[0].message_id == "message-123"
    sent_message = azure_client.begin_send.call_args.args[0]
    assert sent_message["senderAddress"] == "DoNotReply@example.azurecomm.net"
    assert sent_message["content"]["html"] == "<p>Corpo html</p>"
    assert sent_message["attachments"][0]["contentInBase64"] == "YWJj"


def test_azure_provider_raises_runtime_error_on_sdk_failure() -> None:
    app = SimpleNamespace(
        config={
            "MAIL_PROVIDER": "azure",
            "AZURE_EMAIL_ENDPOINT": "https://automatiza-comms.brazil.communication.azure.com/",
            "AZURE_EMAIL_SENDER_ADDRESS": "DoNotReply@example.azurecomm.net",
            "AZURE_COMMUNICATION_CONNECTION_STRING": "endpoint=https://automatiza-comms.brazil.communication.azure.com/;accesskey=test",
        }
    )
    mailer = Mailer(app)
    azure_client = MagicMock()
    azure_client.begin_send.side_effect = ValueError("sender rejected")
    fake_email_module = SimpleNamespace(
        EmailClient=SimpleNamespace(
            from_connection_string=MagicMock(return_value=azure_client)
        )
    )

    with (
        patch(
            "app.mailer.azure_provider.import_module", return_value=fake_email_module
        ),
        pytest.raises(RuntimeError, match="Azure Communication Services"),
    ):
        mailer.send(
            Email(
                to=["destinatario@example.com"],
                subject="Assunto",
                text="Corpo",
            )
        )


def test_smtp_provider_sends_attachment_via_flask_mail(app: Any) -> None:
    app.config["MAIL_PROVIDER"] = "smtp"
    app.config["MAIL_SERVER"] = "localhost"
    app.config["MAIL_PORT"] = 1025
    app.config["MAIL_DEFAULT_SENDER"] = "noreply@example.com"
    mailer = Mailer(app)
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.__exit__.return_value = None

    with (
        app.app_context(),
        patch("app.extensions.mail.connect", return_value=connection),
    ):
        mailer.send(
            Email(
                to=["destinatario@example.com"],
                subject="Assunto",
                text="Corpo",
                attachments=[
                    Attachment(
                        filename="arquivo.csv",
                        content=b"id,nome\n1,teste\n",
                        content_type="text/csv",
                    )
                ],
            )
        )

    sent_message = connection.send.call_args.args[0]
    assert sent_message.subject == "Assunto"
    assert len(sent_message.attachments) == 1
    assert sent_message.attachments[0].filename == "arquivo.csv"


def test_notification_email_includes_csv_attachment() -> None:
    email = notification_email(
        ["destinatario@example.com"],
        _build_report(),
        attach_csv=True,
    )

    assert email.attachments is not None
    assert email.attachments[0].filename.endswith(".csv")


def test_build_notification_emails_uses_individual_recipients(app: Any) -> None:
    with app.app_context():
        app.config["APP_BASE_URL"] = ""
        config = SearchConfig(
            user_id=1,
            label="Alerta teste",
            mail_to=["um@example.com", "dois@example.com"],
            mail_subject="",
            attach_csv=False,
            active=True,
        )
        config.id = 99

        emails = build_notification_emails(
            config=config,
            report=_build_report(),
            secret_key=str(app.config["SECRET_KEY"]),
            app_base_url="",
            app_env="testing",
        )

    assert [email.to for email in emails] == [["um@example.com"], ["dois@example.com"]]
