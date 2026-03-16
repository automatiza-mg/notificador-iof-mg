"""Repositório para operações de banco de dados de SearchConfig."""

from typing import Any, cast

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
        self, config_id: int, user_id: int | None = None
    ) -> SearchConfig | None:
        """Busca config por ID. Se user_id for passado, retorna só se for dono."""
        config = db.session.get(SearchConfig, config_id)
        if config is None:
            return None
        if user_id is not None and config.user_id != user_id:
            return None
        return config

    def find_all(
        self, *, active_only: bool = True, user_id: int | None = None
    ) -> list[SearchConfig]:
        """Lista configs. Se user_id informado, filtra por dono; senão lista todas."""
        query = SearchConfig.query
        if user_id is not None:
            query = query.filter(SearchConfig.user_id == user_id)
        if active_only:
            query = query.filter(SearchConfig.active)
        return cast("list[SearchConfig]", query.all())

    def find_paginated(
        self,
        page: int,
        per_page: int,
        *,
        active_only: bool = True,
        user_id: int | None = None,
    ) -> Any:
        """Lista configs com paginação."""
        query = SearchConfig.query
        if user_id is not None:
            query = query.filter(SearchConfig.user_id == user_id)
        if active_only:
            query = query.filter(SearchConfig.active)
        return query.order_by(SearchConfig.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def delete(self, config: SearchConfig) -> None:
        """Remove uma configuração do banco de dados."""
        db.session.delete(config)
        db.session.commit()

    def add_term(self, term: SearchTerm) -> None:
        """Adiciona termo à sessão (requer commit posterior ou via save)."""
        db.session.add(term)

    def delete_terms_by_config_id(self, config_id: int) -> None:
        """Remove todos os termos associados a uma configuração."""
        SearchTerm.query.filter_by(search_config_id=config_id).delete()

    def commit(self) -> None:
        """Confirma as alterações pendentes na sessão."""
        db.session.commit()
