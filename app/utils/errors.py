"""Utilitários para tratamento de erros."""

from flask import Response, jsonify
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Resposta de erro padronizada."""

    code: str
    message: str
    errors: dict[str, str] | None = None


def server_error(
    message: str = "O servidor encontrou um erro inesperado",
) -> tuple[Response, int]:
    """Retorna erro 500."""
    response = ErrorResponse(code="internal_error", message=message)
    return jsonify(response.model_dump()), 500


def bad_request(
    message: str = "A requisição é mal formada ou inválida",
) -> tuple[Response, int]:
    """Retorna erro 400."""
    response = ErrorResponse(code="bad_request", message=message)
    return jsonify(response.model_dump()), 400


def unauthorized(
    message: str = "Autenticação necessária",
) -> tuple[Response, int]:
    """Retorna erro 401 (não autenticado)."""
    response = ErrorResponse(code="unauthorized", message=message)
    return jsonify(response.model_dump()), 401


def not_found(
    message: str = "O recurso requisitado não foi encontrado",
) -> tuple[Response, int]:
    """Retorna erro 404."""
    response = ErrorResponse(code="not_found", message=message)
    return jsonify(response.model_dump()), 404


def validation_error(errors: dict[str, str]) -> tuple[Response, int]:
    """Retorna erro 422 com erros de validação."""
    response = ErrorResponse(
        code="validation_failed",
        message="Os dados informados são inválidos",
        errors=errors,
    )
    return jsonify(response.model_dump()), 422
