"""Testes para SearchService."""

import pytest
from app.services.search_service import SearchService
from app.repositories.search_config_repository import SearchConfigRepository
from app.schemas.search_config import (
    SearchConfigCreate,
    SearchTermBase,
    SearchConfigUpdate,
)


def test_create_config(app):
    """Testa criação de configuração via serviço."""
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        config_data = SearchConfigCreate(
            label="Service Test",
            terms=[SearchTermBase(term="unit test", exact=True)],
            mail_to=["unit@test.com"],
        )

        config = service.save_config(config_data)

        assert config.id is not None
        assert config.label == "Service Test"
        assert len(config.terms) == 1
        assert config.terms[0].term == "unit test"


def test_update_config(app, sample_config):
    """Testa atualização de configuração."""
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        update_data = SearchConfigUpdate(
            label="Updated Label", terms=[SearchTermBase(term="new term", exact=False)]
        )

        updated = service.update_config(sample_config.id, update_data)

        assert updated.label == "Updated Label"
        assert len(updated.terms) == 1
        assert updated.terms[0].term == "new term"
        assert updated.terms[0].exact is False


def test_list_configs(app, sample_config):
    """Testa listagem de configurações."""
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        configs = service.list_configs()
        assert len(configs) >= 1
        assert configs[0].id == sample_config.id


def test_delete_config(app, sample_config):
    """Testa deleção de configuração."""
    with app.app_context():
        repo = SearchConfigRepository()
        service = SearchService(repo)

        assert service.delete_config(sample_config.id) is True
        assert service.get_config(sample_config.id) is None
