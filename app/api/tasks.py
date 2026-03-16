"""API para tarefas administrativas e processamento."""

import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from app.iof.v1.consulta import consulta_por_data, convert_pages
from app.mailer.mailer import Mailer
from app.mailer.notification import notification_email
from app.repositories.search_config_repository import SearchConfigRepository
from app.search.source import Pagina, SearchSource, Term, Trigger
from app.services.search_service import SearchService

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


def verify_api_key() -> tuple[bool, str | None]:
    """
    Verifica se a API_KEY está presente e é válida.
    Aceita via query parameter (?api_key=...) ou header.

    Returns:
        tuple: (is_valid, error_message)
    """
    expected_key = os.getenv("API_KEY", current_app.config.get("API_KEY", ""))

    if not expected_key:
        return False, "API_KEY não configurada no servidor"

    # Prioridade 1: Query parameter (não passa pela validação de headers do Gunicorn)
    api_key = request.args.get("api_key")

    # Prioridade 2: Tentar headers (pode ser rejeitado pelo Gunicorn)
    if not api_key:
        # Tentar Authorization header (formato: Bearer <token>)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]  # Remove "Bearer "
        else:
            # Fallback para X-API-Key (pode ser rejeitado pelo Gunicorn)
            api_key = request.headers.get("X-API-Key") or request.headers.get(
                "X-API-KEY"
            )

    if not api_key:
        return (
            False,
            "API Key não fornecida. Use ?api_key=... na URL "
            "ou header Authorization: Bearer ...",
        )

    if api_key != expected_key:
        return False, "API Key inválida"

    return True, None


@bp.route("/process-daily", methods=["POST"])
def process_daily() -> tuple[Any, int]:
    """
    Processa o diário oficial de uma data específica.

    Autenticação (escolha uma):
    - Query parameter: ?api_key=<API_KEY> (recomendado, funciona com Gunicorn)
    - Header: Authorization: Bearer <API_KEY> (pode ser rejeitado pelo Gunicorn)
    - Header: X-API-Key: <API_KEY> (pode ser rejeitado pelo Gunicorn)

    Body (JSON opcional):
    {
        "date": "2026-01-14"  # Data no formato YYYY-MM-DD. Se não fornecido, usa hoje.
    }

    Returns:
        JSON com status da execução
    """
    # Verificar autenticação
    is_valid, error_msg = verify_api_key()
    if not is_valid:
        return jsonify({"success": False, "error": error_msg}), 401

    try:
        # Obter data do body ou usar hoje
        data = request.get_json() or {}
        date_str = data.get("date")

        if date_str:
            try:
                publish_date = date.fromisoformat(date_str)
            except ValueError:
                return jsonify(
                    {
                        "success": False,
                        "error": (
                            f"Formato de data inválido: {date_str}. Use YYYY-MM-DD"
                        ),
                    }
                ), 400
        else:
            publish_date = datetime.now(UTC).date()

        # Processar diário (versão síncrona sem RQ)
        current_app.logger.info("Iniciando processamento do diário de %s", publish_date)

        # Chamar função de processamento
        process_daily_gazette_sync(publish_date)

        return jsonify(
            {
                "success": True,
                "message": f"Diário de {publish_date} processado com sucesso",
                "date": publish_date.isoformat(),
            }
        ), 200

    except Exception as e:
        current_app.logger.exception("Erro ao processar diário")
        return jsonify({"success": False, "error": str(e)}), 500


def process_daily_gazette_sync(publish_date: date) -> None:
    """
    Versão síncrona do processamento de diário (sem RQ).

    Args:
        publish_date: Data de publicação do diário
    """
    try:
        # Consultar diário via API v1
        # Consultar diário via API v1
        try:
            response = consulta_por_data(publish_date)
        except Exception as e:
            if "not found" in str(e).lower():
                current_app.logger.info(
                    "Nenhum diário encontrado para %s, pulando...", publish_date
                )
                return
            raise

        # Converter páginas do PDF
        arquivo = response.dados.arquivo_caderno_principal.arquivo
        paginas_iof = convert_pages(arquivo, publish_date)

        # Converter para Pagina do search
        paginas = [
            Pagina(
                titulo="",
                num_pagina=p.num_pagina,
                descricao="",
                conteudo=p.conteudo,
                data_publicacao=p.data_publicacao,
            )
            for p in paginas_iof
        ]

        # Importar páginas no banco de busca
        diarios_dir = current_app.config.get("DIARIOS_DIR", "diarios")
        Path(diarios_dir).mkdir(parents=True, exist_ok=True)
        search_db = str(Path(diarios_dir) / "diarios.db")
        source = SearchSource(search_db)

        try:
            current_app.logger.info("Importando %d páginas...", len(paginas))
            source.import_pages(paginas)

            # Listar configs ativas para notificação
            config_repo = SearchConfigRepository()
            search_service = SearchService(config_repo)
            configs = search_service.list_configs(active_only=True, user_id=None)
            current_app.logger.info("Encontradas %d configurações ativas", len(configs))

            # Processar notificações de forma síncrona (sem RQ)
            for config in configs:
                try:
                    # Chamar função de notificação diretamente (síncrona)
                    notify_search_config_sync(publish_date, config.id)
                    current_app.logger.info(
                        "Notificação processada para config %d", config.id
                    )
                except Exception:
                    current_app.logger.exception(
                        "Erro ao processar notificação para config %d", config.id
                    )
                    # Continuar com outras configurações mesmo se uma falhar

        finally:
            source.close()

    except Exception:
        current_app.logger.exception("Erro ao processar diário")
        raise


def notify_search_config_sync(publish_date: date, config_id: int) -> None:
    """
    Versão síncrona de notify_search_config (sem criar novo app context).
    Busca config sem filtro de usuário (process-daily já listou todas).
    """
    config_repo = SearchConfigRepository()
    search_service = SearchService(config_repo)
    config = search_service.get_config(config_id, user_id=None)
    if not config:
        current_app.logger.warning("Configuração %d não encontrada", config_id)
        return

    # Inicializar source de busca
    diarios_dir = current_app.config.get("DIARIOS_DIR", "diarios")
    search_db = str(Path(diarios_dir) / "diarios.db")
    source = SearchSource(search_db)

    try:
        # Converter termos
        search_terms = [Term(term=term.term, exact=term.exact) for term in config.terms]

        # Gerar relatório
        report = source.lookup(Trigger.CRON, publish_date, search_terms)

        # Se não houver matches, pular
        if report.count == 0:
            current_app.logger.info("Nenhum match encontrado para config %d", config_id)
            return

        # Enviar emails se configurado
        if config.mail_to:
            mailer = Mailer(current_app)
            subject = config.mail_subject or "Novas notificações - Diário Oficial"
            email = notification_email(
                config.mail_to, report, subject=subject, attach_csv=config.attach_csv
            )

            try:
                mailer.send(email)
                csv_info = (
                    " com CSV anexado" if config.attach_csv and report.count > 0 else ""
                )
                current_app.logger.info(
                    "Email enviado para %s (config %d)%s",
                    config.mail_to,
                    config_id,
                    csv_info,
                )
            except Exception:
                current_app.logger.exception("Erro ao enviar email")
                # Não falhar o job por erro de email

    finally:
        source.close()
