"""Rotas de autenticação (login Entra ID, callback, logout)."""

import base64
import json
from urllib.parse import quote

from flask import abort, current_app, make_response, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
import msal

from app.models import User
from app.extensions import db
from app.services.user_service import can_register_new_user


def _decode_id_token_claims(id_token: str) -> dict:
    """Decodifica o payload do JWT id_token (claims). Sem validação de assinatura no MVP."""
    try:
        parts = id_token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return {}


def register(bp):
    """Registra rotas de auth no blueprint web."""

    @bp.route("/login", methods=["GET"])
    def login():
        """Página de login: apenas botão Entrar com Microsoft. Se já logado, redireciona."""
        if current_user.is_authenticated:
            next_url = request.args.get("next") or "/"
            return redirect(next_url)
        error = request.args.get("error")
        return render_template("login.html", error=error)

    @bp.route("/auth/entra/login", methods=["GET"])
    def entra_login():
        """Inicia o fluxo OIDC: guarda next, inicia auth code flow, redireciona para Entra."""
        if current_user.is_authenticated:
            next_url = request.args.get("next") or "/"
            return redirect(next_url)
        next_url = request.args.get("next") or "/"
        session["next"] = next_url

        authority = current_app.config.get("ENTRA_AUTHORITY") or ""
        client_id = current_app.config.get("ENTRA_CLIENT_ID") or ""
        client_secret = current_app.config.get("ENTRA_CLIENT_SECRET") or ""
        redirect_uri = current_app.config.get("ENTRA_REDIRECT_URI") or ""
        scopes_str = current_app.config.get("ENTRA_SCOPES") or "openid profile email"
        # MSAL reserva openid, profile, offline_access e adiciona automaticamente; não passá-los
        _reserved = {"offline_access", "profile", "openid"}
        scopes = [
            s.strip()
            for s in scopes_str.split()
            if s.strip() and s.strip() not in _reserved
        ]

        if not all([authority, client_id, client_secret, redirect_uri]):
            return redirect(url_for("web.login", error="Configuração Entra ID incompleta"))

        app_msal = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority,
        )
        flow = app_msal.initiate_auth_code_flow(scopes=scopes, redirect_uri=redirect_uri)
        if not flow:
            return redirect(url_for("web.login", error="Falha ao iniciar login com Microsoft"))

        auth_uri = flow.get("auth_uri") or flow["auth_uri"]
        auth_uri += "&prompt=select_account" if "?" in auth_uri else "?prompt=select_account"

        state = flow.get("state")
        if state:
            if "msal_flows" not in session:
                session["msal_flows"] = {}
            if "msal_next_by_state" not in session:
                session["msal_next_by_state"] = {}
            session["msal_flows"][state] = flow
            session["msal_next_by_state"][state] = next_url
        else:
            session["msal_flow"] = flow
        # Resposta 200 com redirect via HTML/JS para o cookie de sessão ser gravado antes de
        # ir à Microsoft; em 302 para domínio externo o browser pode não persistir o Set-Cookie
        return render_template("redirect_to_entra.html", auth_uri=auth_uri)

    @bp.route("/auth/callback", methods=["GET"])
    def auth_callback():
        """Callback OIDC: troca code por tokens, provisiona usuário se necessário, login_user."""
        state = request.args.get("state")
        flows = session.get("msal_flows") or {}
        next_by_state = session.get("msal_next_by_state") or {}
        flow = flows.pop(state, None) if state else None
        next_url = next_by_state.pop(state, "/") if state else "/"
        if not flow:
            flow = session.pop("msal_flow", None)
            if not flow:
                next_url = session.pop("next", "/")
            else:
                next_url = session.pop("next", "/") or next_url
        if not flow:
            # Sem code = volta do logout da Microsoft (post_logout_redirect_uri aponta para /auth/callback)
            if not request.args.get("code"):
                return redirect(url_for("web.login"))
            # Callback duplicado ou sessão perdida (ex.: outra aba já completou o login)
            if current_user.is_authenticated:
                return redirect(next_url or "/")
            return redirect(url_for("web.login", error="Sessão expirada. Tente novamente."))

        session["msal_flows"] = flows
        session["msal_next_by_state"] = next_by_state
        session.modified = True

        authority = current_app.config.get("ENTRA_AUTHORITY") or ""
        client_id = current_app.config.get("ENTRA_CLIENT_ID") or ""
        client_secret = current_app.config.get("ENTRA_CLIENT_SECRET") or ""
        redirect_uri = current_app.config.get("ENTRA_REDIRECT_URI") or ""

        app_msal = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority,
        )
        result = app_msal.acquire_token_by_auth_code_flow(flow, request.args)

        if result.get("error"):
            msg = result.get("error_description") or result.get("error") or "Erro de autenticação"
            return redirect(url_for("web.login", error=msg))

        id_token = result.get("id_token")
        if not id_token:
            return redirect(url_for("web.login", error="Resposta da Microsoft sem id_token"))

        id_token_claims = result.get("id_token_claims") or _decode_id_token_claims(id_token)
        oid = id_token_claims.get("oid")
        if not oid:
            return redirect(url_for("web.login", error="Identificador do usuário não encontrado"))

        email_raw = (
            id_token_claims.get("preferred_username")
            or id_token_claims.get("email")
            or id_token_claims.get("upn")
        )
        email = (email_raw or "").strip().lower() or f"{oid}@entra.local"

        user = db.session.query(User).filter_by(
            auth_provider="entra", external_subject=oid
        ).first()

        if not user:
            if not can_register_new_user():
                return render_template("auth_limit_reached.html"), 403
            user = User(
                auth_provider="entra",
                external_subject=oid,
                email=email,
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

        login_user(user)
        return redirect(next_url)

    @bp.route("/logout", methods=["GET", "POST"])
    def logout():
        """Logout: invalida sessão, remove cookie e redireciona para logout da Microsoft.
        Usa ENTRA_REDIRECT_URI (callback) como post_logout_redirect_uri para funcionar com
        apenas uma URI registrada no Azure; o callback redireciona para /login sem erro."""
        logout_user()
        session.clear()
        cookie_name = current_app.config.get("SESSION_COOKIE_NAME", "session")
        authority = (current_app.config.get("ENTRA_AUTHORITY") or "").rstrip("/")
        redirect_uri = current_app.config.get("ENTRA_REDIRECT_URI") or ""
        if not redirect_uri and request.host_url:
            redirect_uri = request.host_url.rstrip("/") + "/auth/callback"
        if authority and redirect_uri:
            logout_path = "/oauth2/v2.0/logout"
            post_logout = quote(redirect_uri, safe="")
            redirect_target = f"{authority}{logout_path}?post_logout_redirect_uri={post_logout}"
        else:
            redirect_target = url_for("web.login")
        resp = make_response(redirect(redirect_target, code=303))
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.delete_cookie(cookie_name, path="/")
        return resp
