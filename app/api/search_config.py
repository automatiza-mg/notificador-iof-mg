"""API para gerenciar configurações de busca."""

import os
import traceback
from datetime import date
from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError
from app.services.search_service import SearchService
from app.repositories.search_config_repository import SearchConfigRepository
from app.repositories.sqlite_document_repository import SQLiteDocumentRepository
from app.schemas.search_config import SearchConfigCreate, SearchConfigUpdate
from app.utils.errors import not_found, validation_error, server_error
from app.iof.v1.consulta import consulta_por_data, convert_pages

bp = Blueprint("search_config", __name__, url_prefix="/api/search/configs")


# Dependency Injection (Simple)
def get_service():
    repository = SearchConfigRepository()
    return SearchService(repository)


def get_doc_repo():
    diarios_dir = current_app.config.get("DIARIOS_DIR", "diarios")
    import os

    os.makedirs(diarios_dir, exist_ok=True)
    search_db = os.path.join(diarios_dir, "diarios.db")
    return SQLiteDocumentRepository(search_db)


def config_to_dict(config):
    """Converte modelo SearchConfig para dicionário."""
    return {
        "id": config.id,
        "label": config.label,
        "description": config.description,
        "attach_csv": config.attach_csv,
        "mail_to": config.mail_to,
        "mail_subject": config.mail_subject,
        "teams_webhook": config.teams_webhook,
        "active": config.active,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        "terms": [{"term": term.term, "exact": term.exact} for term in config.terms],
    }


@bp.route("", methods=["GET"])
def list_configs():
    """Lista todas as configurações de busca."""
    try:
        service = get_service()
        active_only = request.args.get("active_only", "true").lower() == "true"
        configs = service.list_configs(active_only=active_only)
        return jsonify([config_to_dict(c) for c in configs]), 200
    except Exception as e:
        return server_error(str(e))


@bp.route("", methods=["POST"])
def create_config():
    """Cria uma nova configuração de busca."""
    try:
        data = request.get_json()
        if not data:
            return validation_error({"body": "JSON inválido ou vazio"})

        try:
            config_create = SearchConfigCreate(**data)
        except ValidationError as e:
            errors = {}
            for err in e.errors():
                loc = err["loc"]
                field = loc[0] if loc else "body"
                errors[str(field)] = err["msg"]
            return validation_error(errors)

        service = get_service()
        config = service.save_config(config_create)
        return jsonify(config_to_dict(config)), 201
    except Exception as e:
        return server_error(str(e))


@bp.route("/<int:config_id>", methods=["GET"])
def get_config(config_id):
    """Busca uma configuração por ID."""
    try:
        service = get_service()
        config = service.get_config(config_id)
        if not config:
            return not_found()
        return jsonify(config_to_dict(config)), 200
    except Exception as e:
        return server_error(str(e))


@bp.route("/<int:config_id>", methods=["PUT"])
def update_config(config_id):
    """Atualiza uma configuração de busca."""
    try:
        data = request.get_json()
        if not data:
            return validation_error({"body": "JSON inválido ou vazio"})

        try:
            config_update = SearchConfigUpdate(**data)
        except ValidationError as e:
            errors = {}
            for err in e.errors():
                loc = err["loc"]
                field = loc[0] if loc else "body"
                errors[str(field)] = err["msg"]
            return validation_error(errors)

        service = get_service()
        config = service.update_config(config_id, config_update)
        if not config:
            return not_found()
        return jsonify(config_to_dict(config)), 200
    except Exception as e:
        return server_error(str(e))


@bp.route("/<int:config_id>", methods=["DELETE"])
def delete_config(config_id):
    """Deleta uma configuração de busca."""
    try:
        service = get_service()
        deleted = service.delete_config(config_id)
        if not deleted:
            return not_found()
        return "", 204
    except Exception as e:
        return server_error(str(e))


@bp.route("/<int:config_id>/backtest", methods=["GET"])
def backtest_config(config_id):
    """Executa backtest de uma configuração para uma data específica."""
    try:
        # Verificar se backtest está habilitado
        app_env = os.getenv("APP_ENV", "development")
        if app_env != "development":
            return not_found("Backtest disponível apenas em desenvolvimento")

        # Buscar configuração
        service = get_service()
        config = service.get_config(config_id)
        if not config:
            return not_found()

        # Obter data do query string
        date_str = request.args.get("date")
        if not date_str:
            return validation_error({"date": "Parâmetro date é obrigatório"})

        try:
            test_date = date.fromisoformat(date_str)
        except ValueError:
            return validation_error({"date": "Data deve estar no formato YYYY-MM-DD"})

        if test_date > date.today():
            return validation_error({"date": "Não pode ser uma data futura"})

        # Inicializar source de busca e processar
        try:
            doc_repo = get_doc_repo()

            # Verificar se já tem páginas importadas
            has_content = doc_repo.has_content(test_date)

            if not has_content:
                # Baixar e importar diário
                # Import desnecessário removido

                response = consulta_por_data(test_date)
                arquivo = response.dados.arquivo_caderno_principal.arquivo
                paginas_iof = convert_pages(arquivo, test_date)

                # Converter para formato do repositório
                pages_data = [
                    {
                        "titulo": "",
                        "num_pagina": p.num_pagina,
                        "descricao": "",
                        "conteudo": p.conteudo,
                        "data_publicacao": p.data_publicacao,
                    }
                    for p in paginas_iof
                ]
                doc_repo.save_pages(pages_data)

            # Converter termos da config para busca
            search_terms = [
                {"term": term.term, "exact": term.exact} for term in config.terms
            ]

            # Executar busca
            report = doc_repo.search(test_date, search_terms)

            # Converter report para JSON
            result = {
                "publish_date": report.publish_date.isoformat(),
                "highlights": [
                    {
                        "page": h.page,
                        "content": h.content,
                        "term": h.term,
                        "page_url": h.page_url,
                    }
                    for h in report.results
                ],
                "search_terms": [
                    {"term": t.term, "exact": t.exact} for t in config.terms
                ],
                "trigger": "backtest",
                "count": report.count,
            }

            return jsonify(result), 200

        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                return not_found(f"Diário não encontrado para {test_date}")
            current_app.logger.error(
                f"Erro ao baixar diário ou processar backtest: {str(e)}", exc_info=True
            )
            return server_error(str(e))

    except Exception as e:
        current_app.logger.error(
            f"Erro inesperado no backtest: {str(e)}", exc_info=True
        )
        return server_error(str(e))
