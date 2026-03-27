"""Provider Azure Communication Services Email."""

import base64
from importlib import import_module
from typing import Any, Protocol

from app.mailer.message import DeliveryResult, Email
from app.mailer.provider import EmailProvider


class _SendPoller(Protocol):
    def result(self) -> object:
        """Retorna o resultado final do envio."""


class _EmailClientProtocol(Protocol):
    def begin_send(self, message: dict[str, object]) -> _SendPoller:
        """Envia um email via Azure Communication Services."""


class AzureEmailProvider(EmailProvider):
    """Provider de envio via Azure Communication Services Email."""

    provider_name = "azure"

    def __init__(self, app: Any) -> None:
        self.app = app
        self._client: _EmailClientProtocol | None = None

    def validate_configuration(self) -> str | None:
        """Valida a configuração mínima do Azure Email."""
        endpoint = str(self.app.config.get("AZURE_EMAIL_ENDPOINT", "")).strip()
        connection_string = str(
            self.app.config.get("AZURE_COMMUNICATION_CONNECTION_STRING", "")
        ).strip()
        sender_address = str(
            self.app.config.get("AZURE_EMAIL_SENDER_ADDRESS", "")
        ).strip()

        if not endpoint:
            return "Configuração Azure Email ausente. Defina AZURE_EMAIL_ENDPOINT."
        if not connection_string:
            return (
                "Configuração Azure Email ausente. Defina "
                "AZURE_COMMUNICATION_CONNECTION_STRING."
            )
        if not sender_address:
            return (
                "Configuração Azure Email ausente. Defina AZURE_EMAIL_SENDER_ADDRESS."
            )
        return None

    def send(self, *emails: Email) -> list[DeliveryResult]:
        """Envia emails usando o SDK da Azure."""
        config_error = self.validate_configuration()
        if config_error:
            raise RuntimeError(config_error)

        sender_address = str(self.app.config["AZURE_EMAIL_SENDER_ADDRESS"])
        client = self._get_client()
        results: list[DeliveryResult] = []

        try:
            for email in emails:
                poller = client.begin_send(
                    self._build_message(sender_address=sender_address, email=email)
                )
                send_result = poller.result()
                raw_message_id = getattr(send_result, "message_id", None) or getattr(
                    send_result, "id", None
                )
                message_id = str(raw_message_id) if raw_message_id is not None else None
                results.append(
                    DeliveryResult(provider=self.provider_name, message_id=message_id)
                )
        except Exception as exc:
            raise RuntimeError(
                f"Erro ao enviar email via Azure Communication Services: {exc}"
            ) from exc

        return results

    def _get_client(self) -> _EmailClientProtocol:
        if self._client is None:
            email_module = import_module("azure.communication.email")
            email_client_class = email_module.EmailClient
            connection_string = str(
                self.app.config["AZURE_COMMUNICATION_CONNECTION_STRING"]
            )
            self._client = email_client_class.from_connection_string(connection_string)
        return self._client

    def _build_message(self, *, sender_address: str, email: Email) -> dict[str, object]:
        message: dict[str, object] = {
            "senderAddress": sender_address,
            "recipients": {
                "to": [{"address": recipient} for recipient in email.to],
            },
            "content": {
                "subject": email.subject,
                "plainText": email.text,
            },
        }

        content = message["content"]
        if isinstance(content, dict) and email.html:
            content["html"] = email.html

        if email.attachments:
            message["attachments"] = [
                {
                    "name": attachment.filename,
                    "contentType": attachment.content_type,
                    "contentInBase64": base64.b64encode(attachment.content).decode(
                        "ascii"
                    ),
                }
                for attachment in email.attachments
            ]

        return message
