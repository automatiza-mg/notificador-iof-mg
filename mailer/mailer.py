"""Cliente de email para envio de notificações."""
from dataclasses import dataclass
from typing import List, Optional
from flask import current_app
from flask_mail import Mail, Message


@dataclass
class Email:
    """Estrutura de email."""
    to: List[str]
    subject: str
    text: str
    html: Optional[str] = None


class Mailer:
    """Cliente para envio de emails."""
    
    def __init__(self, app=None):
        """
        Inicializa o mailer.
        
        Args:
            app: Instância do Flask app (opcional, pode usar current_app)
        """
        self.mail = Mail()
        if app:
            self.mail.init_app(app)
    
    def init_app(self, app):
        """Inicializa mailer com app Flask."""
        self.mail.init_app(app)
    
    def send(self, *emails: Email) -> None:
        """
        Envia um ou mais emails.
        
        Args:
            *emails: Emails para enviar
            
        Raises:
            RuntimeError: Se houver erro ao enviar
        """
        if not self.mail:
            # Tentar usar current_app
            from flask import has_app_context, current_app
            if has_app_context():
                self.mail = Mail(current_app)
            else:
                raise RuntimeError("Mailer não inicializado. Chame init_app() ou passe app no construtor.")
        
        messages = []
        for email in emails:
            msg = Message(
                subject=email.subject,
                recipients=email.to,
                body=email.text,
                html=email.html
            )
            messages.append(msg)
        
        try:
            with self.mail.connect() as conn:
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
            text="Este é um email de teste do sistema de notificações do Diário Oficial de MG."
        )
        self.send(email)

