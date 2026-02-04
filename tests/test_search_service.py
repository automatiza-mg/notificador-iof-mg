"""Testes para SearchService (multi-tenant por user_id)."""

import pytest
from app.services.search_service import SearchService
from app.repositories.search_config_repository import SearchConfigRepository
from app.schemas.search_config import (
    SearchConfigCreate,
    SearchTermBase,
    SearchConfigUpdate,
)


def test_create_config(app, test_user):
    """Testa criação de configuração via serviço (com user_id)."""
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        config_data = SearchConfigCreate(
            label="Service Test",
            terms=[SearchTermBase(term="unit test", exact=True)],
            mail_to=["unit@test.com"],
        )

        config = service.save_config(config_data, user_id=test_user.id)

        assert config.id is not None
        assert config.label == "Service Test"
        assert config.user_id == test_user.id
        assert len(config.terms) == 1
        assert config.terms[0].term == "unit test"


def test_update_config(app, sample_config, test_user):
    """Testa atualização de configuração (com user_id para ownership)."""
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        update_data = SearchConfigUpdate(
            label="Updated Label", terms=[SearchTermBase(term="new term", exact=False)]
        )

        updated = service.update_config(
            sample_config.id, update_data, user_id=test_user.id
        )

        assert updated is not None
        assert updated.label == "Updated Label"
        assert len(updated.terms) == 1
        assert updated.terms[0].term == "new term"
        assert updated.terms[0].exact is False


def test_list_configs(app, sample_config, test_user):
    """Testa listagem de configurações (filtrada por user_id)."""
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        configs = service.list_configs(user_id=test_user.id)
        assert len(configs) >= 1
        assert configs[0].id == sample_config.id
        assert configs[0].user_id == test_user.id


def test_delete_config(app, sample_config, test_user):
    """Testa deleção de configuração (com user_id para ownership)."""
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        assert service.delete_config(sample_config.id, user_id=test_user.id) is True
        assert service.get_config(sample_config.id, user_id=test_user.id) is None


def test_get_config_returns_none_for_other_user(app, sample_config, test_user_b):
    """get_config com user_id de outro usuário retorna None (IDOR)."""
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)
        # sample_config pertence a test_user, não test_user_b
        config = service.get_config(sample_config.id, user_id=test_user_b.id)
        assert config is None
