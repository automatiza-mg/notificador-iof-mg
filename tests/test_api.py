"""Testes para a API de Configurações e autenticação Entra ID (mock)."""

import pytest
from unittest.mock import patch, MagicMock


def test_login_page_has_microsoft_button_no_password_form(client):
    """GET /login exibe botão Entrar com conta Microsoft - CAMG e não tem form de senha."""
    response = client.get("/login")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Entrar com conta Microsoft - CAMG" in html
    assert "/auth/entra/login" in html
    assert 'name="password"' not in html


def test_login_redirects_when_authenticated(client_logged_in):
    """GET /login com usuário já logado redireciona para / (ou next)."""
    response = client_logged_in.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/" or response.location.endswith("/")
    response_next = client_logged_in.get("/login?next=/configs/new", follow_redirects=False)
    assert response_next.status_code == 302
    assert "/configs/new" in (response_next.location or "")


def test_entra_login_redirects_when_authenticated(client_logged_in, app):
    """GET /auth/entra/login com usuário já logado redireciona para /."""
    with app.app_context():
        app.config["ENTRA_AUTHORITY"] = "https://login.microsoftonline.com/tenant"
        app.config["ENTRA_CLIENT_ID"] = "client-id"
        app.config["ENTRA_CLIENT_SECRET"] = "secret"
        app.config["ENTRA_REDIRECT_URI"] = "http://localhost:5000/auth/callback"
    response = client_logged_in.get("/auth/entra/login", follow_redirects=False)
    assert response.status_code == 302
    assert "login.microsoftonline.com" not in (response.location or "")
    assert response.location == "/" or response.location.endswith("/")


def test_callback_no_flow_redirects_when_authenticated(client_logged_in):
    """Callback sem flow na sessão (ex.: callback duplicado) com usuário já logado redireciona para /."""
    response = client_logged_in.get("/auth/callback?code=any&state=any", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" not in (response.location or "")
    assert response.location == "/" or response.location.endswith("/")


def test_entra_login_redirects_to_auth_uri(client, app):
    """GET /auth/entra/login inicia flow e devolve página que redireciona para Entra com prompt=select_account."""
    fake_flow = {
        "auth_uri": "https://login.microsoftonline.com/tenant/oauth2/v2.0/authorize?state=abc",
        "state": "abc",
    }
    with app.app_context():
        app.config["ENTRA_AUTHORITY"] = "https://login.microsoftonline.com/tenant"
        app.config["ENTRA_CLIENT_ID"] = "client-id"
        app.config["ENTRA_CLIENT_SECRET"] = "secret"
        app.config["ENTRA_REDIRECT_URI"] = "http://localhost:5000/auth/callback"
        app.config["ENTRA_SCOPES"] = "openid profile email"
    with patch("app.web.auth.msal.ConfidentialClientApplication") as MockApp:
        mock_instance = MagicMock()
        mock_instance.initiate_auth_code_flow.return_value = fake_flow
        MockApp.return_value = mock_instance
        response = client.get("/auth/entra/login?next=/", follow_redirects=False)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "login.microsoftonline.com" in html
    assert "prompt=select_account" in html


def test_callback_success_provisions_user_and_logs_in(app, client):
    """Callback com token válido cria usuário Entra (se não existir) e autentica."""
    with app.app_context():
        from app.models import User
        assert User.query.filter_by(auth_provider="entra", external_subject="oid-123").first() is None
    fake_flow = {"state": "x", "auth_uri": "https://example.com"}
    fake_result = {
        "id_token": "a.b.c",
        "id_token_claims": {"oid": "oid-123", "preferred_username": "user@org.com"},
    }
    with client.session_transaction() as sess:
        sess["msal_flow"] = fake_flow
        sess["next"] = "/"
    with patch("app.web.auth.msal.ConfidentialClientApplication") as MockApp:
        mock_instance = MagicMock()
        mock_instance.acquire_token_by_auth_code_flow.return_value = fake_result
        MockApp.return_value = mock_instance
        app.config["ENTRA_AUTHORITY"] = "https://login.microsoftonline.com/t"
        app.config["ENTRA_CLIENT_ID"] = "c"
        app.config["ENTRA_CLIENT_SECRET"] = "s"
        app.config["ENTRA_REDIRECT_URI"] = "http://localhost:5000/auth/callback"
        response = client.get("/auth/callback?code=code&state=x", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/" or response.location.endswith("/")
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(auth_provider="entra", external_subject="oid-123").first()
        assert user is not None
        assert user.email == "user@org.com"
    r2 = client.get("/")
    assert r2.status_code == 200


def test_callback_cap_100_returns_403_and_does_not_create_user(app, client):
    """Com 100 usuários Entra, callback com novo oid retorna 403 e não cria usuário."""
    with app.app_context():
        from app.models import User
        from app.extensions import db
        n = User.query.filter_by(auth_provider="entra").count()
        for i in range(100 - n):
            u = User(
                email=f"cap{i+100}@entra.local",
                auth_provider="entra",
                external_subject=f"oid-cap-{i+100}",
            )
            db.session.add(u)
        db.session.commit()
        assert User.query.filter_by(auth_provider="entra").count() >= 100
    fake_flow = {"state": "y", "auth_uri": "https://example.com"}
    fake_result = {
        "id_token": "a.b.c",
        "id_token_claims": {"oid": "new-oid-never-seen", "preferred_username": "new@org.com"},
    }
    with client.session_transaction() as sess:
        sess["msal_flow"] = fake_flow
        sess["next"] = "/"
    with patch("app.web.auth.msal.ConfidentialClientApplication") as MockApp:
        mock_instance = MagicMock()
        mock_instance.acquire_token_by_auth_code_flow.return_value = fake_result
        MockApp.return_value = mock_instance
        app.config["ENTRA_AUTHORITY"] = "https://login.microsoftonline.com/t"
        app.config["ENTRA_CLIENT_ID"] = "c"
        app.config["ENTRA_CLIENT_SECRET"] = "s"
        app.config["ENTRA_REDIRECT_URI"] = "http://localhost:5000/auth/callback"
        response = client.get("/auth/callback?code=code&state=y", follow_redirects=False)
    assert response.status_code == 403
    with app.app_context():
        from app.models import User
        assert User.query.filter_by(external_subject="new-oid-never-seen").first() is None


def test_callback_existing_user_logs_in_when_cap_reached(app, client):
    """Com cap atingido, usuário já existente (mesmo oid) ainda consegue login."""
    with app.app_context():
        from app.models import User
        from app.extensions import db
        existing = User(
            email="existing@org.com",
            auth_provider="entra",
            external_subject="oid-existing-100",
        )
        db.session.add(existing)
        for i in range(99):
            u = User(
                email=f"cap{i}@entra.local",
                auth_provider="entra",
                external_subject=f"oid-cap-{i}",
            )
            db.session.add(u)
        db.session.commit()
    fake_flow = {"state": "z", "auth_uri": "https://example.com"}
    fake_result = {
        "id_token": "a.b.c",
        "id_token_claims": {"oid": "oid-existing-100", "preferred_username": "existing@org.com"},
    }
    with client.session_transaction() as sess:
        sess["msal_flow"] = fake_flow
        sess["next"] = "/"
    with patch("app.web.auth.msal.ConfidentialClientApplication") as MockApp:
        mock_instance = MagicMock()
        mock_instance.acquire_token_by_auth_code_flow.return_value = fake_result
        MockApp.return_value = mock_instance
        app.config["ENTRA_AUTHORITY"] = "https://login.microsoftonline.com/t"
        app.config["ENTRA_CLIENT_ID"] = "c"
        app.config["ENTRA_CLIENT_SECRET"] = "s"
        app.config["ENTRA_REDIRECT_URI"] = "http://localhost:5000/auth/callback"
        response = client.get("/auth/callback?code=code&state=z", follow_redirects=False)
    assert response.status_code == 302
    r2 = client.get("/")
    assert r2.status_code == 200


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
    with client.session_transaction() as sess:
        sess["_user_id"] = str(test_user_b.id)
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

    r_list = client.get("/api/search/configs")
    assert r_list.status_code == 200
    ids = [c["id"] for c in r_list.get_json()]
    assert config_id not in ids
