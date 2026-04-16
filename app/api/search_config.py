"""API para gerenciar configurações de busca (protegida por sessão Flask-Login)."""

import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError

from app.iof.v1.consulta import consulta_por_data, convert_pages
from app.models.search_config import SearchConfig
from app.repositories.search_config_repository import SearchConfigRepository
from app.repositories.sqlite_document_repository import SQLiteDocumentRepository
from app.schemas.search_config import SearchConfigCreate, SearchConfigUpdate
from app.services.search_service import SearchService
from app.utils.errors import not_found, server_error, validation_error

bp = Blueprint("search_config", __name__, url_prefix="/api/search/configs")


# Dependency Injection (Simple)
def get_service() -> SearchService:
    repository = SearchConfigRepository()
    return SearchService(repository)


def get_doc_repo() -> SQLiteDocumentRepository:
    diarios_dir = current_app.config.get("DIARIOS_DIR", "diarios")

    Path(diarios_dir).mkdir(parents=True, exist_ok=True)
    search_db = str(Path(diarios_dir) / "diarios.db")
    return SQLiteDocumentRepository(search_db)


def config_to_dict(config: SearchConfig) -> dict[str, Any]:
    """Converte modelo SearchConfig para dicionário."""
    return {
        "id": config.id,
        "label": config.label,
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
@login_required
def list_configs() -> tuple[Any, int]:
    """Lista configurações de busca do usuário logado."""
    service = get_service()
    active_only = request.args.get("active_only", "true").lower() == "true"
    configs = service.list_configs(active_only=active_only, user_id=current_user.id)
    return jsonify([config_to_dict(c) for c in configs]), 200


@bp.route("", methods=["POST"])
@login_required
def create_config() -> tuple[Any, int]:
    """Cria uma nova configuração de busca (do usuário logado)."""
    data = request.get_json()
    if not data:
        return validation_error({"body": "JSON inválido ou vazio"})

    try:
        config_create = SearchConfigCreate.model_validate(data)
    except ValidationError as e:
        errors = {}
        for err in e.errors():
            loc = err["loc"]
            field = loc[0] if loc else "body"
            errors[str(field)] = err["msg"]
        return validation_error(errors)

    service = get_service()
    config = service.save_config(config_create, user_id=current_user.id)
    return jsonify(config_to_dict(config)), 201


@bp.route("/<int:config_id>", methods=["GET"])
@login_required
def get_config(config_id: int) -> tuple[Any, int]:
    """Busca uma configuração por ID (apenas do dono)."""
    service = get_service()
    config = service.get_config(config_id, user_id=current_user.id)
    if not config:
        return not_found()
    return jsonify(config_to_dict(config)), 200


@bp.route("/<int:config_id>", methods=["PUT"])
@login_required
def update_config(config_id: int) -> tuple[Any, int]:
    """Atualiza uma configuração de busca (apenas do dono)."""
    data = request.get_json()
    if not data:
        return validation_error({"body": "JSON inválido ou vazio"})

    try:
        config_update = SearchConfigUpdate.model_validate(data)
    except ValidationError as e:
        errors = {}
        for err in e.errors():
            loc = err["loc"]
            field = loc[0] if loc else "body"
            errors[str(field)] = err["msg"]
        return validation_error(errors)

    service = get_service()
    config = service.update_config(config_id, config_update, user_id=current_user.id)
    if not config:
        return not_found()
    return jsonify(config_to_dict(config)), 200


@bp.route("/<int:config_id>", methods=["DELETE"])
@login_required
def delete_config(config_id: int) -> tuple[Any, int]:
    """Deleta uma configuração de busca (apenas do dono)."""
    service = get_service()
    deleted = service.delete_config(config_id, user_id=current_user.id)
    if not deleted:
        return not_found()
    return "", 204


@bp.route("/<int:config_id>/backtest", methods=["GET"])
@login_required
def backtest_config(config_id: int) -> tuple[Any, int]:
    """Executa backtest de uma configuração (apenas do dono)."""
    try:
        # Verificar se backtest está habilitado
        app_env = os.getenv("APP_ENV", "development")
        if app_env != "development":
            return not_found("Backtest disponível apenas em desenvolvimento")

        # Buscar configuração (ownership)
        service = get_service()
        config = service.get_config(config_id, user_id=current_user.id)
        if not config:
            return not_found()

        # Obter data do query string
        date_str = request.args.get("date")
        test_date: date | None = None
        error_dict = None
        if not date_str:
            error_dict = {"date": "Parâmetro date é obrigatório"}
        else:
            try:
                test_date = date.fromisoformat(date_str)
                if test_date > datetime.now(UTC).date():
                    error_dict = {"date": "Não pode ser uma data futura"}
            except ValueError:
                error_dict = {"date": "Data deve estar no formato YYYY-MM-DD"}

        if error_dict:
            return validation_error(error_dict)
        if test_date is None:
            return validation_error({"date": "Data inválida"})

        # Inicializar source de busca e processar
        try:
            doc_repo = get_doc_repo()

            # Verificar se já tem páginas importadas
            has_content = doc_repo.has_content(test_date)

            if not has_content:
                # Baixar e importar diário
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
            current_app.logger.exception("Erro ao baixar diário ou processar backtest")
            return server_error(str(e))

    except Exception as e:
        current_app.logger.exception("Erro inesperado no backtest")
        return server_error(str(e))
