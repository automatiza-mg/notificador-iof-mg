"""Interface para o repositório de documentos (FTS)."""

from abc import ABC, abstractmethod
from datetime import date
from typing import List
from dataclasses import dataclass


@dataclass
class SearchResult:
    page: int
    content: str
    term: str
    page_url: str


@dataclass
class SearchReport:
    publish_date: date
    results: List[SearchResult]
    count: int


class DocumentRepository(ABC):
    """Interface abstrata para repositório de documentos."""

    @abstractmethod
    def save_pages(self, pages: List[dict]) -> None:
        """Salva páginas no índice."""
        pass

    @abstractmethod
    def search(self, date: date, terms: List[dict]) -> SearchReport:
        """Busca termos em uma data."""
        pass

    @abstractmethod
    def has_content(self, date: date) -> bool:
        """Verifica se há conteúdo para a data."""
        pass
