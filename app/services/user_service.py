"""Serviço de usuários (limite para futura integração Entra ID)."""

from app.models import User

# Limite de usuários únicos para cadastro via Entra ID (primeiros 100).
# Não usado no fluxo local (sem autocadastro); reservado para callback Entra.
USER_CAP_ENTRA = 100


def can_register_new_user() -> bool:
    """
    Indica se ainda é permitido registrar um novo usuário via Entra ID.

    Conta apenas usuários com auth_provider="entra". Os 100 primeiros podem
    ser criados no primeiro login; a partir do 101º, bloquear criação
    (mostrar "limite atingido"), mas permitir login dos já cadastrados.
    """
    return User.query.filter_by(auth_provider="entra").count() < USER_CAP_ENTRA
