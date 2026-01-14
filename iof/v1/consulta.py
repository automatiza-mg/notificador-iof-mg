"""Consulta à API v1 do Diário Oficial."""
import base64
import requests
from dataclasses import dataclass
from datetime import date
from typing import List, Optional
from urllib.parse import urlencode

from iof.client import Pagina, ErrNotFound
from pdf.extractor import PDFExtractor


V1_BASE_URL = "https://www.jornalminasgerais.mg.gov.br/api/v1/Jornal/ObterEdicaoPorDataPublicacao"


@dataclass
class ArquivoCadernoPrincipal:
    """Arquivo do caderno principal em Base64."""
    arquivo: str
    arquivo_unico: bool
    pagina: int
    total_paginas: int
    descricao_caderno: str


@dataclass
class Secao:
    """Seção do caderno."""
    descricao: str
    pagina_inicial: int


@dataclass
class Caderno:
    """Caderno do diário."""
    id: int
    descricao: str
    ordem: int
    secoes: List[Secao]


@dataclass
class Dados:
    """Dados da resposta da API."""
    data_publicacao: str
    cadernos: List[Caderno]
    arquivo_caderno_principal: ArquivoCadernoPrincipal


@dataclass
class Response:
    """Resposta da API v1."""
    dados: Dados


def consulta_por_data(publish_date: date) -> Response:
    """
    Consulta diário por data usando API v1.
    
    Args:
        publish_date: Data de publicação
        
    Returns:
        Resposta da API com dados do diário
        
    Raises:
        ErrNotFound: Se não houver diário para a data
        requests.RequestException: Se houver erro na requisição
    """
    params = urlencode({
        'dataPublicacao': publish_date.strftime('%Y-%m-%d')
    })
    url = f"{V1_BASE_URL}?{params}"
    
    response = requests.get(url, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        dados = data.get('dados', {})
        
        # Parsear cadernos
        cadernos = []
        for cad in dados.get('cadernos', []):
            secoes = [
                Secao(
                    descricao=sec.get('descricao', ''),
                    pagina_inicial=sec.get('paginaInicial', 0)
                )
                for sec in cad.get('secoes', [])
            ]
            cadernos.append(Caderno(
                id=cad.get('id', 0),
                descricao=cad.get('descricao', ''),
                ordem=cad.get('ordem', 0),
                secoes=secoes
            ))
        
        # Parsear arquivo caderno principal
        arquivo_data = dados.get('arquivoCadernoPrincipal', {})
        arquivo = ArquivoCadernoPrincipal(
            arquivo=arquivo_data.get('arquivo', ''),
            arquivo_unico=arquivo_data.get('arquivoUnico', False),
            pagina=arquivo_data.get('pagina', 0),
            total_paginas=arquivo_data.get('totalPaginas', 0),
            descricao_caderno=arquivo_data.get('descricaoCaderno', '')
        )
        
        return Response(
            dados=Dados(
                data_publicacao=dados.get('dataPublicacao', ''),
                cadernos=cadernos,
                arquivo_caderno_principal=arquivo
            )
        )
    elif response.status_code == 401:
        raise ErrNotFound(f"Diário não encontrado para {publish_date}")
    else:
        raise requests.RequestException(
            f"Unexpected status: {response.status_code}"
        )


def convert_pages(arquivo_base64: str, publish_date: date) -> List[Pagina]:
    """
    Converte arquivo Base64 em lista de páginas.
    
    Args:
        arquivo_base64: PDF em Base64
        publish_date: Data de publicação
        
    Returns:
        Lista de páginas extraídas
        
    Raises:
        ValueError: Se houver erro ao decodificar Base64
        RuntimeError: Se houver erro na extração
    """
    # Decodificar Base64
    try:
        pdf_bytes = base64.b64decode(arquivo_base64)
    except Exception as e:
        raise ValueError(f"Erro ao decodificar Base64: {e}") from e
    
    # Extrair páginas
    extractor = PDFExtractor()
    pdf_pages = extractor.extract_pages(pdf_bytes)
    
    # Converter para Pagina do IOF
    paginas = []
    for pdf_page in pdf_pages:
        paginas.append(Pagina(
            titulo="",
            num_pagina=pdf_page.number,
            descricao="",
            conteudo=pdf_page.content,
            data_publicacao=publish_date
        ))
    
    return paginas

