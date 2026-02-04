"""Rotas de autenticação (login/logout)."""

from flask import redirect, render_template, request, url_for
from flask_login import login_user, logout_user

from app.models import User
from app.extensions import db


def register(bp):
    """Registra rotas de auth no blueprint web."""

    @bp.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            if not email or not password:
                return render_template(
                    "login.html", error="E-mail e senha são obrigatórios."
                ), 400
            user = db.session.query(User).filter_by(email=email).first()
            if user is None or not user.check_password(password):
                return render_template(
                    "login.html", error="E-mail ou senha incorretos."
                ), 401
            login_user(user)
            next_url = request.args.get("next") or url_for("web.index")
            return redirect(next_url)
        return render_template("login.html")

    @bp.route("/logout", methods=["GET", "POST"])
    def logout():
        logout_user()
        return redirect(url_for("web.index"))
