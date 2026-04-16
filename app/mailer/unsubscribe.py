"""Helpers para links de descadastro em emails."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from itsdangerous import URLSafeTimedSerializer

UNSUBSCRIBE_SALT = "unsubscribe-email"
DEFAULT_LOCAL_BASE_URL = "http://localhost:5000"


@dataclass(frozen=True, slots=True)
class UnsubscribePayload:
    """Dados assinados no token de descadastro."""

    config_id: int
    email: str


def _get_serializer(secret_key: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=secret_key, salt=UNSUBSCRIBE_SALT)


def normalize_email(email: str) -> str:
    """Normaliza email para comparação e assinatura."""
    return email.strip().lower()


def generate_unsubscribe_token(*, config_id: int, email: str, secret_key: str) -> str:
    """Gera token assinado para descadastro de um alerta."""
    serializer = _get_serializer(secret_key)
    return str(
        serializer.dumps(
            {
                "config_id": config_id,
                "email": normalize_email(email),
            }
        )
    )


def load_unsubscribe_token(
    *, token: str, secret_key: str, max_age_seconds: int
) -> UnsubscribePayload:
    """Carrega e valida token de descadastro."""
    serializer = _get_serializer(secret_key)
    data = serializer.loads(token, max_age=max_age_seconds)
    config_id = int(data["config_id"])
    email = normalize_email(str(data["email"]))
    return UnsubscribePayload(config_id=config_id, email=email)


def resolve_app_base_url(*, configured_base_url: str, app_env: str) -> str:
    """Resolve base URL absoluta usada nos links enviados por email."""
    base_url = configured_base_url.strip().rstrip("/")
    if base_url:
        return base_url
    if app_env in {"development", "testing"}:
        return DEFAULT_LOCAL_BASE_URL
    raise RuntimeError(
        "APP_BASE_URL não configurada. Defina APP_BASE_URL para gerar links "
        "de descadastro em produção."
    )


def build_unsubscribe_url(*, app_base_url: str, token: str) -> str:
    """Monta URL absoluta de descadastro."""
    query = urlencode({"token": token})
    return f"{app_base_url.rstrip('/')}/unsubscribe?{query}"
