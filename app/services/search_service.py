"""Serviço para gerenciar configurações de busca."""

from typing import List, Optional
from app.models.search_config import SearchConfig, SearchTerm
from app.schemas.search_config import SearchConfigCreate, SearchConfigUpdate
from app.repositories.search_config_repository import SearchConfigRepository


class SearchService:
    """Serviço para operações CRUD de configurações de busca (multi-tenant por user_id)."""

    def __init__(self, repository: SearchConfigRepository):
        self.repository = repository

    def save_config(self, config_data: SearchConfigCreate, user_id: int) -> SearchConfig:
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
            description=config_data.description or "",
            attach_csv=config_data.attach_csv,
            mail_to=mail_to,
            mail_subject=config_data.mail_subject or "",
            teams_webhook=webhook,
            active=config_data.active,
        )

        for term_data in config_data.terms:
            term = SearchTerm(term=term_data.term, exact=term_data.exact)
            config.terms.append(term)

        return self.repository.save(config)

    def get_config(
        self, config_id: int, user_id: Optional[int] = None
    ) -> Optional[SearchConfig]:
        """
        Busca uma configuração por ID. Se user_id for informado, só retorna se for dono.
        """
        return self.repository.get_by_id(config_id, user_id=user_id)

    def list_configs(
        self, active_only: bool = True, user_id: Optional[int] = None
    ) -> List[SearchConfig]:
        """
        Lista configurações. Se user_id for informado, apenas do dono; senão todas (uso em process-daily).
        """
        return self.repository.find_all(active_only=active_only, user_id=user_id)

    def update_config(
        self,
        config_id: int,
        config_data: SearchConfigUpdate,
        user_id: Optional[int] = None,
    ) -> Optional[SearchConfig]:
        """
        Atualiza uma configuração existente. Se user_id for informado, só atualiza se for dono.
        """
        config = self.repository.get_by_id(config_id, user_id=user_id)
        if not config:
            return None

        # Atualizar campos apenas se foram fornecidos (não None)
        if config_data.label is not None:
            config.label = config_data.label
        if config_data.description is not None:
            config.description = config_data.description
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
                    exact=term_data.exact,
                    search_config_id=config.id,
                )
                self.repository.add_term(term)

        return self.repository.save(config)

    def delete_config(
        self, config_id: int, user_id: Optional[int] = None
    ) -> bool:
        """
        Deleta uma configuração. Se user_id for informado, só deleta se for dono.
        """
        config = self.repository.get_by_id(config_id, user_id=user_id)
        if not config:
            return False

        self.repository.delete(config)
        return True
