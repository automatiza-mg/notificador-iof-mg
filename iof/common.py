"""Classes e exceções comuns para o módulo IOF."""
from dataclasses import dataclass
from datetime import date


class ErrNotFound(Exception):
    """Erro quando diário não é encontrado."""
    pass


@dataclass
class Pagina:
    """Página do Diário Oficial."""
    titulo: str
    num_pagina: int
    descricao: str
    conteudo: str
    data_publicacao: date
