"""Schemas Pydantic para validação e tipagem de SearchConfig."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, HttpUrl, Field, ConfigDict


class SearchTermBase(BaseModel):
    """Schema base para termo de busca."""

    term: str = Field(..., min_length=1, description="Termo a ser buscado")
    exact: bool = Field(default=True, description="Se a busca deve ser exata")


class SearchConfigBase(BaseModel):
    """Schema base com campos comuns de configuração."""

    label: str = Field(
        ..., min_length=1, max_length=100, description="Nome da configuração"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Descrição opcional"
    )
    attach_csv: bool = Field(
        default=False, description="Anexar CSV com resultados no email"
    )
    mail_to: List[EmailStr] = Field(
        default_factory=list,
        max_length=5,
        description="Lista de emails para notificação",
    )
    mail_subject: Optional[str] = Field(
        None, max_length=200, description="Assunto personalizado do email"
    )
    teams_webhook: Optional[HttpUrl] = Field(
        None, description="Webhook do MS Teams (opcional)"
    )
    active: bool = Field(default=True, description="Se a configuração está ativa")


class SearchConfigCreate(SearchConfigBase):
    """Schema para criação de configuração."""

    terms: List[SearchTermBase] = Field(
        ..., min_length=1, max_length=5, description="Lista de termos (1 a 5)"
    )


class SearchConfigUpdate(BaseModel):
    """Schema para atualização (todos campos opcionais)."""

    label: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    attach_csv: Optional[bool] = None
    mail_to: Optional[List[EmailStr]] = Field(None, max_length=5)
    mail_subject: Optional[str] = Field(None, max_length=200)
    teams_webhook: Optional[HttpUrl] = None
    active: Optional[bool] = None
    terms: Optional[List[SearchTermBase]] = Field(None, min_length=1, max_length=5)


class SearchConfigResponse(SearchConfigBase):
    """Schema para resposta (leitura)."""

    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    terms: List[SearchTermBase]

    model_config = ConfigDict(from_attributes=True)
