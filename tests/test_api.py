"""Testes para a API de Configurações."""

import pytest


def test_list_configs_api(client, sample_config):
    """Testa endpoint de listagem."""
    response = client.get("/api/search/configs")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
    assert data[0]["label"] == sample_config.label


def test_create_config_api(client):
    """Testa endpoint de criação com validação."""
    # Caso de sucesso
    payload = {
        "label": "API Test",
        "terms": [{"term": "api", "exact": True}],
        "mail_to": ["api@test.com"],
    }
    response = client.post("/api/search/configs", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["label"] == "API Test"

    # Caso de erro (email inválido)
    payload_invalid = {
        "label": "Invalid",
        "terms": [{"term": "test"}],
        "mail_to": ["not-email"],
    }
    response = client.post("/api/search/configs", json=payload_invalid)
    assert response.status_code == 422
    data = response.get_json()
    assert "mail_to" in str(data["errors"])


def test_get_config_api(client, sample_config):
    """Testa endpoint de detalhe."""
    response = client.get(f"/api/search/configs/{sample_config.id}")
    assert response.status_code == 200
    assert response.get_json()["id"] == sample_config.id


def test_update_config_api(client, sample_config):
    """Testa endpoint de atualização."""
    payload = {"label": "API Updated"}
    response = client.put(f"/api/search/configs/{sample_config.id}", json=payload)
    assert response.status_code == 200
    assert response.get_json()["label"] == "API Updated"


def test_delete_config_api(client, sample_config):
    """Testa endpoint de deleção."""
    response = client.delete(f"/api/search/configs/{sample_config.id}")
    assert response.status_code == 204

    # Verificar se sumiu
    response = client.get(f"/api/search/configs/{sample_config.id}")
    assert response.status_code == 404
