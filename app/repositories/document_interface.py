"""Interface para o repositório de documentos (FTS)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class SearchResult:
    page: int
    content: str
    term: str
    page_url: str


@dataclass
class SearchReport:
    publish_date: date
    results: list[SearchResult]
    count: int


class DocumentRepository(ABC):
    """Interface abstrata para repositório de documentos."""

    @abstractmethod
    def save_pages(self, pages: list[dict[str, Any]]) -> None:
        """Salva páginas no índice."""

    @abstractmethod
    def search(self, publish_date: date, terms: list[dict[str, Any]]) -> SearchReport:
        """Busca termos em uma data."""

    @abstractmethod
    def has_content(self, publish_date: date) -> bool:
        """Verifica se há conteúdo para a data."""
