"""Contratos para providers de envio de email."""

from abc import ABC, abstractmethod

from app.mailer.message import DeliveryResult, Email


class EmailProvider(ABC):
    """Contrato base para providers de email."""

    provider_name: str

    @abstractmethod
    def validate_configuration(self) -> str | None:
        """Retorna erro de configuração ou ``None`` se estiver tudo pronto."""

    @abstractmethod
    def send(self, *emails: Email) -> list[DeliveryResult]:
        """Envia emails usando o provider."""
