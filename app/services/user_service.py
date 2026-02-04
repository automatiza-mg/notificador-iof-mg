"""Serviço de usuários (limite para futura integração Entra ID)."""

from app.models import User

# Limite de usuários únicos para cadastro via Entra ID (primeiros 100).
# Não usado no fluxo local (sem autocadastro); reservado para callback Entra.
USER_CAP_ENTRA = 100


def can_register_new_user() -> bool:
    """
    Indica se ainda é permitido registrar um novo usuário (ex.: via Entra ID).

    Regra futura: os 100 primeiros usuários únicos (contas Entra) podem ser
    criados no primeiro login; a partir do 101º, bloquear criação e mostrar
    "limite atingido", mas permitir login dos já cadastrados.

    Nesta entrega (apenas auth local), não é chamado em nenhum fluxo;
    deixado pronto para uso no callback OIDC do Entra ID.
    """
    return User.query.count() < USER_CAP_ENTRA
