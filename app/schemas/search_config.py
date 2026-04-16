"""Schemas Pydantic para validação e tipagem de SearchConfig."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class SearchTermBase(BaseModel):
    """Schema base para termo de busca."""

    term: str = Field(..., min_length=1, description="Termo a ser buscado")
    exact: bool = Field(default=True, description="Se a busca deve ser exata")


class SearchConfigBase(BaseModel):
    """Schema base com campos comuns de configuração."""

    label: str = Field(
        ..., min_length=1, max_length=100, description="Nome da configuração"
    )
    attach_csv: bool = Field(
        default=False, description="Anexar CSV com resultados no email"
    )
    mail_to: list[EmailStr] = Field(
        default_factory=list,
        max_length=5,
        description="Lista de emails para notificação",
    )
    mail_subject: str | None = Field(
        None, max_length=200, description="Assunto personalizado do email"
    )
    teams_webhook: HttpUrl | None = Field(
        None, description="Webhook do MS Teams (opcional)"
    )
    active: bool = Field(default=True, description="Se a configuração está ativa")


class SearchConfigCreate(SearchConfigBase):
    """Schema para criação de configuração."""

    terms: list[SearchTermBase] = Field(
        ..., min_length=1, max_length=5, description="Lista de termos (1 a 5)"
    )


class SearchConfigUpdate(BaseModel):
    """Schema para atualização (todos campos opcionais)."""

    label: str | None = Field(None, min_length=1, max_length=100)
    attach_csv: bool | None = None
    mail_to: list[EmailStr] | None = Field(None, max_length=5)
    mail_subject: str | None = Field(None, max_length=200)
    teams_webhook: HttpUrl | None = None
    active: bool | None = None
    terms: list[SearchTermBase] | None = Field(None, min_length=1, max_length=5)


class SearchConfigResponse(SearchConfigBase):
    """Schema para resposta (leitura)."""

    id: int
    created_at: datetime | None
    updated_at: datetime | None
    terms: list[SearchTermBase]

    model_config = ConfigDict(from_attributes=True)
