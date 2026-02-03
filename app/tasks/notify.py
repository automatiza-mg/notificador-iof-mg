"""Worker para enviar notificações."""

from datetime import date
from app import create_app
from app.extensions import db
from app.services.search_service import SearchService
from app.search.source import SearchSource, Term, Trigger
from app.mailer.mailer import Mailer
from app.mailer.notification import notification_email
import os


def notify_search_config(publish_date_str: str, config_id: int) -> None:
    """
    Envia notificações para uma configuração de busca.

    Args:
        publish_date_str: Data de publicação no formato ISO (YYYY-MM-DD)
        config_id: ID da configuração de busca
    """
    app = create_app()
    with app.app_context():
        try:
            # Parsear data
            publish_date = date.fromisoformat(publish_date_str)

            # Buscar configuração
            config = SearchService.get_config(config_id)
            if not config:
                print(f"Configuração {config_id} não encontrada")
                return

            # Inicializar source de busca
            diarios_dir = app.config.get("DIARIOS_DIR", "diarios")
            search_db = os.path.join(diarios_dir, "diarios.db")
            source = SearchSource(search_db)

            try:
                # Converter termos
                search_terms = [
                    Term(term=term.term, exact=term.exact) for term in config.terms
                ]

                # Gerar relatório
                report = source.lookup(Trigger.CRON, publish_date, search_terms)

                # Se não houver matches, pular
                if report.count == 0:
                    print(f"Nenhum match encontrado para config {config_id}")
                    return

                # Enviar emails se configurado
                if config.mail_to:
                    mailer = Mailer(app)
                    subject = (
                        config.mail_subject or "Novas notificações - Diário Oficial"
                    )
                    email = notification_email(
                        config.mail_to,
                        report,
                        subject=subject,
                        attach_csv=config.attach_csv,
                    )

                    try:
                        mailer.send(email)
                        csv_info = (
                            " com CSV anexado"
                            if config.attach_csv and report.count > 0
                            else ""
                        )
                        print(
                            f"Email enviado para {config.mail_to} (config {config_id}){csv_info}"
                        )
                    except Exception as e:
                        print(f"Erro ao enviar email: {e}")
                        # Não falhar o job por erro de email

            finally:
                source.close()

        except Exception as e:
            print(f"Erro ao processar notificação: {e}")
            import traceback

            traceback.print_exc()
            raise
