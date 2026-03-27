"""Modelos internos de email usados pelos providers."""

from dataclasses import dataclass


@dataclass(slots=True)
class Attachment:
    """Estrutura de anexo de email."""

    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass(slots=True)
class Email:
    """Estrutura de email."""

    to: list[str]
    subject: str
    text: str
    html: str | None = None
    attachments: list[Attachment] | None = None


@dataclass(slots=True)
class DeliveryResult:
    """Resultado do envio de um email por um provider."""

    provider: str
    message_id: str | None = None
