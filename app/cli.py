"""Comandos CLI do Flask (criar usuário, seed de teste)."""

import click
from app.extensions import db
from app.models import User


def register_commands(app):
    """Registra comandos CLI no app."""

    @app.cli.command("create-user")
    @click.option("--email", required=True, help="E-mail do usuário")
    @click.option("--password", required=True, hide_input=True, prompt=True)
    def create_user(email, password):
        """Cria um usuário local (auth_provider=local)."""
        with app.app_context():
            email = email.strip().lower()
            if not email or not password:
                click.echo("E-mail e senha são obrigatórios.", err=True)
                raise SystemExit(1)
            existing = db.session.query(User).filter_by(email=email).first()
            if existing:
                click.echo(f"Usuário com e-mail {email} já existe.", err=True)
                raise SystemExit(1)
            user = User(
                email=email,
                auth_provider="local",
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            click.echo(f"Usuário criado: {email} (id={user.id})")

    @app.cli.command("seed-test-users")
    def seed_test_users():
        """Cria 2 usuários de teste (apenas se ainda não existirem)."""
        with app.app_context():
            test_users = [
                ("teste1@exemplo.com", "senha123"),
                ("teste2@exemplo.com", "senha123"),
            ]
            created = 0
            for email, password in test_users:
                email = email.strip().lower()
                if db.session.query(User).filter_by(email=email).first():
                    click.echo(f"Já existe: {email}")
                    continue
                user = User(email=email, auth_provider="local")
                user.set_password(password)
                db.session.add(user)
                created += 1
                click.echo(f"Criado: {email}")
            db.session.commit()
            click.echo(f"Total: {created} usuário(s) de teste criado(s).")
