"""Utilitários para tratamento de erros."""
from typing import Dict, Optional
from flask import jsonify
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Resposta de erro padronizada."""
    code: str
    message: str
    errors: Optional[Dict[str, str]] = None


def server_error(message: str = "O servidor encontrou um erro inesperado") -> tuple:
    """Retorna erro 500."""
    response = ErrorResponse(
        code="internal_error",
        message=message
    )
    return jsonify(response.model_dump()), 500


def bad_request(message: str = "A requisição é mal formada ou inválida") -> tuple:
    """Retorna erro 400."""
    response = ErrorResponse(
        code="bad_request",
        message=message
    )
    return jsonify(response.model_dump()), 400


def not_found(message: str = "O recurso requisitado não foi encontrado") -> tuple:
    """Retorna erro 404."""
    response = ErrorResponse(
        code="not_found",
        message=message
    )
    return jsonify(response.model_dump()), 404


def validation_error(errors: Dict[str, str]) -> tuple:
    """Retorna erro 422 com erros de validação."""
    response = ErrorResponse(
        code="validation_failed",
        message="Os dados informados são inválidos",
        errors=errors
    )
    return jsonify(response.model_dump()), 422

