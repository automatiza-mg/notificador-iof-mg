"""Modelo de usuário para autenticação e multi-tenancy."""

from __future__ import annotations

from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def get_now_utc():
    """Retorna o datetime atual em UTC."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Usuário do sistema (autenticação local ou Entra ID)."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("auth_provider", "external_subject", name="uq_users_provider_subject"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="local")
    external_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=get_now_utc
    )

    # Relacionamento com configurações de busca (multi-tenancy)
    search_configs: Mapped[list["SearchConfig"]] = relationship(
        "SearchConfig", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Define o hash da senha (nunca armazenar em texto puro)."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica se a senha confere com o hash armazenado."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email}>"
