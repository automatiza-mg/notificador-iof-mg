"""Classes e exceções comuns para o módulo IOF."""

from dataclasses import dataclass
from datetime import date


class NotFoundError(Exception):
    """Erro quando diário não é encontrado."""


@dataclass
class Pagina:
    """Página do Diário Oficial."""

    titulo: str
    num_pagina: int
    descricao: str
    conteudo: str
    data_publicacao: date
