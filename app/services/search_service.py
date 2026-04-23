"""Serviço para gerenciar configurações de busca."""

from dataclasses import dataclass
from typing import Any

from app.mailer.unsubscribe import normalize_email
from app.models.search_config import SearchConfig, SearchTerm
from app.repositories.search_config_repository import SearchConfigRepository
from app.schemas.search_config import SearchConfigCreate, SearchConfigUpdate


@dataclass(frozen=True, slots=True)
class UnsubscribeResult:
    """Resultado do descadastro de um email em um alerta."""

    status: str
    config: SearchConfig | None
    email: str
    deactivated: bool = False


class SearchService:
    """Serviço para operações CRUD de configurações de busca (multi-tenant)."""

    def __init__(self, repository: SearchConfigRepository) -> None:
        self.repository = repository

    def save_config(
        self, config_data: SearchConfigCreate, user_id: int
    ) -> SearchConfig:
        """
        Salva uma nova configuração de busca (sempre associada a um usuário).

        Args:
            config_data: Objeto Pydantic com dados da configuração
            user_id: ID do usuário dono da configuração

        Returns:
            Configuração salva
        """
        mail_to = [str(e) for e in config_data.mail_to] if config_data.mail_to else []
        webhook = str(config_data.teams_webhook) if config_data.teams_webhook else None

        config = SearchConfig(
            user_id=user_id,
            label=config_data.label,
            attach_csv=config_data.attach_csv,
            mail_to=mail_to,
            mail_subject=config_data.mail_subject or "",
            teams_webhook=webhook,
            active=config_data.active,
        )

        for term_data in config_data.terms:
            term = SearchTerm(term=term_data.term, exact=True)
            config.terms.append(term)

        return self.repository.save(config)

    def get_config(
        self, config_id: int, user_id: int | None = None
    ) -> SearchConfig | None:
        """
        Busca uma configuração por ID. Se user_id for informado, só retorna se for dono.
        """
        return self.repository.get_by_id(config_id, user_id=user_id)

    def list_configs(
        self, *, active_only: bool = True, user_id: int | None = None
    ) -> list[SearchConfig]:
        """
        Lista configurações. Se user_id for informado, apenas do dono; senão todas.
        """
        return self.repository.find_all(active_only=active_only, user_id=user_id)

    def list_configs_paginated(
        self,
        page: int,
        per_page: int,
        *,
        active_only: bool = True,
        user_id: int | None = None,
    ) -> Any:
        """
        Lista configurações com paginação. Se user_id for informado, apenas do dono.
        """
        return self.repository.find_paginated(
            page, per_page, active_only=active_only, user_id=user_id
        )

    def update_config(
        self,
        config_id: int,
        config_data: SearchConfigUpdate,
        user_id: int | None = None,
    ) -> SearchConfig | None:
        """
        Atualiza config existente. Se user_id informado, só atualiza se for dono.
        """
        config = self.repository.get_by_id(config_id, user_id=user_id)
        if not config:
            return None

        # Atualizar campos apenas se foram fornecidos (não None)
        if config_data.label is not None:
            config.label = config_data.label
        if config_data.attach_csv is not None:
            config.attach_csv = config_data.attach_csv
        if config_data.mail_to is not None:
            config.mail_to = [str(e) for e in config_data.mail_to]
        if config_data.mail_subject is not None:
            config.mail_subject = config_data.mail_subject
        if config_data.teams_webhook is not None:
            config.teams_webhook = str(config_data.teams_webhook)
        if config_data.active is not None:
            config.active = config_data.active

        # Atualizar termos apenas se a lista foi fornecida (mesmo que vazia)
        if config_data.terms is not None:
            # Remover termos antigos via repositório
            self.repository.delete_terms_by_config_id(config_id)

            # Limpar lista em memória para evitar conflitos se o flush não ocorreu
            config.terms = []

            # Adicionar novos termos
            for term_data in config_data.terms:
                term = SearchTerm(
                    term=term_data.term,
                    exact=True,
                    search_config_id=config.id,
                )
                self.repository.add_term(term)

        return self.repository.save(config)

    def delete_config(self, config_id: int, user_id: int | None = None) -> bool:
        """
        Deleta uma configuração. Se user_id for informado, só deleta se for dono.
        """
        config = self.repository.get_by_id(config_id, user_id=user_id)
        if not config:
            return False

        self.repository.delete(config)
        return True

    def unsubscribe_email_from_config(
        self, config_id: int, email: str
    ) -> UnsubscribeResult:
        """Remove um email de um alerta e inativa se ele ficar sem destinatários."""
        normalized_email = normalize_email(email)
        config = self.repository.get_by_id(config_id, user_id=None)
        if not config:
            return UnsubscribeResult(
                status="not_found",
                config=None,
                email=normalized_email,
            )

        normalized_mail_to = [normalize_email(address) for address in config.mail_to]
        if normalized_email not in normalized_mail_to:
            return UnsubscribeResult(
                status="already_removed",
                config=config,
                email=normalized_email,
            )

        remaining_mail_to = [
            original_email
            for original_email in config.mail_to
            if normalize_email(original_email) != normalized_email
        ]
        config.mail_to = remaining_mail_to

        deactivated = False
        if not remaining_mail_to:
            config.active = False
            deactivated = True

        saved_config = self.repository.save(config)
        return UnsubscribeResult(
            status="removed",
            config=saved_config,
            email=normalized_email,
            deactivated=deactivated,
        )
