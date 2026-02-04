"""Modelos SQLAlchemy."""
from app.models.user import User
from app.models.search_config import SearchConfig, SearchTerm

__all__ = ["User", "SearchConfig", "SearchTerm"]

