"""Serviço para gerenciar configurações de busca."""

from typing import List, Optional
from app.models.search_config import SearchConfig, SearchTerm
from app.schemas.search_config import SearchConfigCreate, SearchConfigUpdate
from app.repositories.search_config_repository import SearchConfigRepository


class SearchService:
    """Serviço para operações CRUD de configurações de busca."""

    def __init__(self, repository: SearchConfigRepository):
        self.repository = repository

    def save_config(self, config_data: SearchConfigCreate) -> SearchConfig:
        """
        Salva uma nova configuração de busca.

        Args:
            config_data: Objeto Pydantic com dados da configuração

        Returns:
            Configuração salva
        """
        # Converter EmailStr e HttpUrl para strings simples se necessário
        mail_to = [str(e) for e in config_data.mail_to] if config_data.mail_to else []
        webhook = str(config_data.teams_webhook) if config_data.teams_webhook else None

        config = SearchConfig(
            label=config_data.label,
            description=config_data.description or "",
            attach_csv=config_data.attach_csv,
            mail_to=mail_to,
            mail_subject=config_data.mail_subject or "",
            teams_webhook=webhook,
            active=config_data.active,
        )

        # O repositório lida com session.add, mas precisamos lidar com os termos
        # Como o relacionamento cascade geralmente requer que o pai esteja na sessão,
        # vamos usar o save inicial para garantir ID se necessário, ou construir o grafo de objetos completo.

        # Estratégia: Construir objetos, adicionar termos ao objeto config, salvar tudo via repositório.

        for term_data in config_data.terms:
            term = SearchTerm(term=term_data.term, exact=term_data.exact)
            config.terms.append(term)

        return self.repository.save(config)

    def get_config(self, config_id: int) -> Optional[SearchConfig]:
        """
        Busca uma configuração por ID.

        Args:
            config_id: ID da configuração

        Returns:
            Configuração encontrada ou None
        """
        return self.repository.get_by_id(config_id)

    def list_configs(self, active_only: bool = True) -> List[SearchConfig]:
        """
        Lista todas as configurações.

        Args:
            active_only: Se True, retorna apenas configurações ativas

        Returns:
            Lista de configurações
        """
        return self.repository.find_all(active_only=active_only)

    def update_config(
        self, config_id: int, config_data: SearchConfigUpdate
    ) -> Optional[SearchConfig]:
        """
        Atualiza uma configuração existente.

        Args:
            config_id: ID da configuração
            config_data: Objeto Pydantic com dados atualizados

        Returns:
            Configuração atualizada ou None se não encontrada
        """
        config = self.repository.get_by_id(config_id)
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

    def delete_config(self, config_id: int) -> bool:
        """
        Deleta uma configuração.

        Args:
            config_id: ID da configuração

        Returns:
            True se deletada, False se não encontrada
        """
        config = self.repository.get_by_id(config_id)
        if not config:
            return False

        self.repository.delete(config)
        return True
