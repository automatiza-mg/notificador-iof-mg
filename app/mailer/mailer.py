"""Fachada para envio de emails usando providers configuráveis."""

from typing import Any

from app.mailer.azure_provider import AzureEmailProvider
from app.mailer.message import DeliveryResult, Email
from app.mailer.provider import EmailProvider
from app.mailer.smtp_provider import SmtpEmailProvider


class Mailer:
    """Cliente para envio de emails."""

    def __init__(self, app: Any = None) -> None:
        """
        Inicializa o mailer.

        Args:
            app: Instância do Flask app (opcional, pode usar current_app)
        """
        self.app = app
        self._provider: EmailProvider | None = None

    @property
    def provider_name(self) -> str:
        """Nome do provider atualmente configurado."""
        provider_name = str(self._get_app().config.get("MAIL_PROVIDER", "smtp")).strip()
        return provider_name.lower() or "smtp"

    def validate_configuration(self) -> str | None:
        """Valida a configuração do provider atual."""
        return self._get_provider().validate_configuration()

    def send(self, *emails: Email) -> list[DeliveryResult]:
        """
        Envia um ou mais emails.

        Args:
            *emails: Emails para enviar

        Returns:
            Metadados de envio retornados pelo provider
        """
        return self._get_provider().send(*emails)

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

    def _get_app(self) -> Any:
        from flask import current_app, has_app_context  # noqa: PLC0415

        app_to_use = self.app or (current_app if has_app_context() else None)
        if app_to_use is None:
            raise RuntimeError(
                "Mailer não inicializado. Requer contexto de aplicação Flask."
            )
        return app_to_use

    def _get_provider(self) -> EmailProvider:
        if self._provider is None:
            app = self._get_app()
            provider_name = self.provider_name
            if provider_name == "azure":
                self._provider = AzureEmailProvider(app)
            elif provider_name == "smtp":
                self._provider = SmtpEmailProvider(app)
            else:
                raise RuntimeError(
                    f"Provider de email desconhecido: {provider_name}. "
                    "Use 'azure' ou 'smtp'."
                )
        return self._provider
