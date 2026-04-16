"""Worker para enviar notificações."""

from datetime import date
from pathlib import Path

from app import create_app
from app.mailer.mailer import Mailer
from app.mailer.notification import build_notification_emails
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
                    emails = build_notification_emails(
                        config=config,
                        report=report,
                        secret_key=str(app.config["SECRET_KEY"]),
                        app_base_url=str(app.config.get("APP_BASE_URL", "")),
                        app_env=str(app.config.get("APP_ENV", "development")),
                    )

                    try:
                        results = mailer.send(*emails)
                        csv_info = (
                            " com CSV anexado"
                            if config.attach_csv and report.count > 0
                            else ""
                        )
                        message_id = results[0].message_id if results else None
                        app.logger.info(
                            "Email enviado via %s para %s (config %s)%s%s",
                            mailer.provider_name,
                            config.mail_to,
                            config_id,
                            csv_info,
                            f" [message_id={message_id}]" if message_id else "",
                        )
                    except Exception:
                        app.logger.exception("Erro ao enviar email")
                        # Não falhar o job por erro de email

            finally:
                source.close()

        except Exception:
            app.logger.exception("Erro ao processar notificação")
            raise
