"""Cliente de email para envio de notificações."""

from dataclasses import dataclass
from typing import Any

from flask_mail import Message


@dataclass
class Attachment:
    """Estrutura de anexo de email."""

    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class Email:
    """Estrutura de email."""

    to: list[str]
    subject: str
    text: str
    html: str | None = None
    attachments: list[Attachment] | None = None


class Mailer:
    """Cliente para envio de emails."""

    def __init__(self, app: Any = None) -> None:
        """
        Inicializa o mailer.

        Args:
            app: Instância do Flask app (opcional, pode usar current_app)
        """
        self.app = app
        self._mail: Any = None

    def _get_mail(self) -> Any:
        """Obtém a instância do Mail, usando a já inicializada no app se disponível."""
        if self._mail is None:
            from flask import current_app, has_app_context  # noqa: PLC0415

            app_to_use = self.app or (current_app if has_app_context() else None)

            if app_to_use:
                # Usar a instância já inicializada do mail no app
                from app.extensions import mail  # noqa: PLC0415

                self._mail = mail
            else:
                raise RuntimeError(
                    "Mailer não inicializado. Requer contexto de aplicação Flask."
                )

        return self._mail

    def send(self, *emails: Email) -> None:
        """
        Envia um ou mais emails.

        Args:
            *emails: Emails para enviar

        Raises:
            RuntimeError: Se houver erro ao enviar
        """
        mail = self._get_mail()

        messages = []
        for email in emails:
            _recipients: list[str | tuple[str, str]] = []
            _recipients.extend(email.to)
            msg = Message(
                subject=email.subject,
                recipients=_recipients,
                body=email.text,
                html=email.html,
            )

            # Adicionar anexos se houver
            if email.attachments:
                for attachment in email.attachments:
                    msg.attach(
                        filename=attachment.filename,
                        content_type=attachment.content_type,
                        data=attachment.content,
                    )

            messages.append(msg)

        try:
            with mail.connect() as conn:
                for msg in messages:
                    conn.send(msg)
        except Exception as e:
            raise RuntimeError(f"Erro ao enviar email: {e}") from e

    def send_test_email(self, to: str) -> None:
        """
        Envia email de teste.

        Args:
            to: Endereço de email de destino
        """
        email = Email(
            to=[to],
            subject="Teste - Notificador IOF MG",
            text="Este é um email de teste do sistema de notificações.",
        )
        self.send(email)
