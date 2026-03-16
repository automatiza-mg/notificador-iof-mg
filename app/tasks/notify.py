"""Worker para enviar notificações."""

from datetime import date
from pathlib import Path

from app import create_app
from app.mailer.mailer import Mailer
from app.mailer.notification import notification_email
from app.repositories.search_config_repository import SearchConfigRepository
from app.search.source import SearchSource, Term, Trigger
from app.services.search_service import SearchService


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

            # Buscar configuração (sem filtro de usuário
            # job já validado pelo processamento)
            config_repo = SearchConfigRepository()
            search_service = SearchService(config_repo)
            config = search_service.get_config(config_id, user_id=None)
            if not config:
                app.logger.warning("Configuração %s não encontrada", config_id)
                return

            # Inicializar source de busca
            diarios_dir = app.config.get("DIARIOS_DIR", "diarios")
            search_db = str(Path(diarios_dir) / "diarios.db")
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
                    app.logger.info("Nenhum match encontrado para config %s", config_id)
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
                        app.logger.info(
                            "Email enviado para %s (config %s)%s",
                            config.mail_to,
                            config_id,
                            csv_info,
                        )
                    except Exception:
                        app.logger.exception("Erro ao enviar email")
                        # Não falhar o job por erro de email

            finally:
                source.close()

        except Exception:
            app.logger.exception("Erro ao processar notificação")
            raise
