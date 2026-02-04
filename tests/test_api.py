"""Testes para a API de Configurações (com autenticação e multi-tenant)."""

import pytest


def test_login_success(client, test_user):
    """Login com credenciais corretas redireciona e autentica."""
    response = client.post(
        "/login",
        data={"email": test_user.email, "password": "testpass123"},
        follow_redirects=False,
    )
    assert response.status_code in (200, 302)
    # Após login, acessar index deve funcionar (não redirect para login)
    response2 = client.get("/")
    assert response2.status_code == 200


def test_login_wrong_password(client, test_user):
    """Login com senha errada retorna erro."""
    response = client.post(
        "/login",
        data={"email": test_user.email, "password": "wrongpass"},
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_api_configs_require_login(client):
    """API de configs retorna 401 quando não autenticado."""
    response = client.get("/api/search/configs")
    assert response.status_code == 401
    data = response.get_json()
    assert data.get("code") == "unauthorized"

    response_post = client.post(
        "/api/search/configs",
        json={"label": "x", "terms": [{"term": "y", "exact": True}], "mail_to": []},
    )
    assert response_post.status_code == 401


def test_list_configs_api(client_logged_in, sample_config):
    """Testa endpoint de listagem (apenas configs do usuário)."""
    response = client_logged_in.get("/api/search/configs")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
    assert data[0]["label"] == sample_config.label


def test_create_config_api(client_logged_in):
    """Testa endpoint de criação com validação."""
    payload = {
        "label": "API Test",
        "terms": [{"term": "api", "exact": True}],
        "mail_to": ["api@test.com"],
    }
    response = client_logged_in.post("/api/search/configs", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["label"] == "API Test"

    payload_invalid = {
        "label": "Invalid",
        "terms": [{"term": "test"}],
        "mail_to": ["not-email"],
    }
    response = client_logged_in.post("/api/search/configs", json=payload_invalid)
    assert response.status_code == 422
    data = response.get_json()
    assert "mail_to" in str(data["errors"])


def test_get_config_api(client_logged_in, sample_config):
    """Testa endpoint de detalhe."""
    response = client_logged_in.get(f"/api/search/configs/{sample_config.id}")
    assert response.status_code == 200
    assert response.get_json()["id"] == sample_config.id


def test_update_config_api(client_logged_in, sample_config):
    """Testa endpoint de atualização."""
    payload = {"label": "API Updated"}
    response = client_logged_in.put(
        f"/api/search/configs/{sample_config.id}", json=payload
    )
    assert response.status_code == 200
    assert response.get_json()["label"] == "API Updated"


def test_delete_config_api(client_logged_in, sample_config):
    """Testa endpoint de deleção."""
    response = client_logged_in.delete(f"/api/search/configs/{sample_config.id}")
    assert response.status_code == 204

    response = client_logged_in.get(f"/api/search/configs/{sample_config.id}")
    assert response.status_code == 404


def test_multi_tenant_user_b_cannot_access_user_a_config(
    app, client, test_user, test_user_b, sample_config
):
    """Usuário B não consegue acessar/editar/deletar config do usuário A (404)."""
    # sample_config pertence a test_user (A). Logar como B.
    client.post(
        "/login",
        data={"email": test_user_b.email, "password": "passb123"},
        follow_redirects=True,
    )
    config_id = sample_config.id

    r_get = client.get(f"/api/search/configs/{config_id}")
    assert r_get.status_code == 404

    r_put = client.put(
        f"/api/search/configs/{config_id}",
        json={"label": "Hacked"},
    )
    assert r_put.status_code == 404

    r_del = client.delete(f"/api/search/configs/{config_id}")
    assert r_del.status_code == 404

    # Listagem de B não deve incluir a config de A
    r_list = client.get("/api/search/configs")
    assert r_list.status_code == 200
    ids = [c["id"] for c in r_list.get_json()]
    assert config_id not in ids
