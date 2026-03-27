"""Provider SMTP baseado em Flask-Mail."""

from typing import Any, cast

from flask_mail import Message

from app.mailer.message import DeliveryResult, Email
from app.mailer.provider import EmailProvider


class SmtpEmailProvider(EmailProvider):
    """Provider de envio via SMTP."""

    provider_name = "smtp"

    def __init__(self, app: Any) -> None:
        self.app = app

    def validate_configuration(self) -> str | None:
        """Valida a configuração SMTP mínima para envio."""
        mail_server = str(self.app.config.get("MAIL_SERVER", "")).strip()
        if not mail_server:
            return (
                "Configuração SMTP ausente. Defina MAIL_SMTP_HOST para usar email em "
                "desenvolvimento."
            )
        return None

    def send(self, *emails: Email) -> list[DeliveryResult]:
        """Envia emails usando a extensão Flask-Mail."""
        config_error = self.validate_configuration()
        if config_error:
            raise RuntimeError(config_error)

        from app.extensions import mail  # noqa: PLC0415

        messages = [self._build_message(email) for email in emails]

        try:
            with mail.connect() as conn:
                for message in messages:
                    conn.send(message)
        except Exception as exc:
            raise RuntimeError(f"Erro ao enviar email via SMTP: {exc}") from exc

        return [DeliveryResult(provider=self.provider_name) for _ in emails]

    def _build_message(self, email: Email) -> Message:
        recipients = cast("list[str | tuple[str, str]]", email.to.copy())
        message = Message(
            subject=email.subject,
            recipients=recipients,
            body=email.text,
            html=email.html,
        )

        if email.attachments:
            for attachment in email.attachments:
                message.attach(
                    filename=attachment.filename,
                    content_type=attachment.content_type,
                    data=attachment.content,
                )

        return message
