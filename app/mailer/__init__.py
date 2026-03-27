"""Sistema de envio de emails."""

from app.mailer.mailer import Mailer
from app.mailer.message import Attachment, Email

__all__ = ["Attachment", "Email", "Mailer"]
