"""Modelos para configurações de busca."""

import json
from datetime import datetime, timezone
from typing import List

from sqlalchemy import (
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


def get_now_utc():
    """Retorna o datetime atual em UTC."""
    return datetime.now(timezone.utc)


class ListType(TypeDecorator):
    """Tipo customizado para armazenar listas como JSON (compatível com SQLite e PostgreSQL)."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Converte lista para JSON string ao salvar."""
        if value is None:
            return json.dumps([])  # Retorna lista vazia como JSON
        if isinstance(value, list):
            return json.dumps(value)
        # Se já for string JSON, retorna como está
        if isinstance(value, str):
            return value
        return json.dumps([])

    def process_result_value(self, value, dialect):
        """Converte JSON string para lista ao ler."""
        if value is None:
            return []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        return value


class SearchConfig(db.Model):
    """Configuração de busca no Diário Oficial."""

    __tablename__ = "search_configs"

    # Usar Integer para compatibilidade com SQLite (autoincrement funciona melhor)
    # Em PostgreSQL, Integer suporta até 2 bilhões, suficiente para a maioria dos casos
    # Se precisar de mais, podemos usar BigInteger apenas em PostgreSQL
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attach_csv: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mail_to: Mapped[List[str]] = mapped_column(ListType, nullable=False, default=list)
    mail_subject: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    teams_webhook: Mapped[str] = mapped_column(Text, nullable=True, default=None)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=get_now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_now_utc,
        onupdate=get_now_utc,
    )

    # Relacionamento com usuário (multi-tenancy)
    user: Mapped["User"] = relationship("User", back_populates="search_configs")

    # Relacionamento com termos
    terms: Mapped[List["SearchTerm"]] = relationship(
        "SearchTerm", back_populates="search_config", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SearchConfig {self.id}: {self.label}>"


class SearchTerm(db.Model):
    """Termo de busca associado a uma configuração."""

    __tablename__ = "search_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(Text, nullable=False)
    exact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    search_config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("search_configs.id", ondelete="CASCADE"), nullable=False
    )

    # Relacionamento com configuração
    search_config: Mapped["SearchConfig"] = relationship(
        "SearchConfig", back_populates="terms"
    )

    def __repr__(self) -> str:
        return f"<SearchTerm {self.id}: {self.term} (exact={self.exact})>"
