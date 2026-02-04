"""Repositório para operações de banco de dados de SearchConfig."""

from typing import List, Optional
from app.extensions import db
from app.models.search_config import SearchConfig, SearchTerm


class SearchConfigRepository:
    """Repositório para gerenciar a persistência de configurações de busca."""

    def save(self, config: SearchConfig) -> SearchConfig:
        """Salva uma nova configuração ou atualiza uma existente."""
        db.session.add(config)
        db.session.commit()
        db.session.refresh(config)
        return config

    def get_by_id(
        self, config_id: int, user_id: Optional[int] = None
    ) -> Optional[SearchConfig]:
        """Busca uma configuração pelo ID. Se user_id for informado, só retorna se for dono."""
        config = db.session.get(SearchConfig, config_id)
        if config is None:
            return None
        if user_id is not None and config.user_id != user_id:
            return None
        return config

    def find_all(
        self, active_only: bool = True, user_id: Optional[int] = None
    ) -> List[SearchConfig]:
        """Lista configurações. Se user_id for informado, filtra por dono; senão lista todas."""
        query = SearchConfig.query
        if user_id is not None:
            query = query.filter(SearchConfig.user_id == user_id)
        if active_only:
            query = query.filter(SearchConfig.active == True)
        return query.all()

    def delete(self, config: SearchConfig) -> None:
        """Remove uma configuração do banco de dados."""
        db.session.delete(config)
        db.session.commit()

    def add_term(self, term: SearchTerm) -> None:
        """Adiciona um termo à sessão (requer commit posterior ou via save da config)."""
        db.session.add(term)

    def delete_terms_by_config_id(self, config_id: int) -> None:
        """Remove todos os termos associados a uma configuração."""
        SearchTerm.query.filter_by(search_config_id=config_id).delete()

    def commit(self) -> None:
        """Confirma as alterações pendentes na sessão."""
        db.session.commit()
