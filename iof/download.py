"""Download de PDFs do Diário Oficial."""
import requests
from datetime import date
from typing import Tuple, List
from iof.client import ErrNotFound
from pdf.extractor import PDFExtractor, Page


def download_pdf(publish_date: date) -> bytes:
    """
    Baixa o PDF do diário oficial para uma data.
    
    Args:
        publish_date: Data de publicação
        
    Returns:
        Conteúdo do PDF em bytes
        
    Raises:
        ErrNotFound: Se o PDF não for encontrado
        requests.RequestException: Se houver erro na requisição
    """
    url = (
        f"https://www.jornalminasgerais.mg.gov.br/modulos/"
        f"www.jornalminasgerais.mg.gov.br//diarioOficial/"
        f"{publish_date.strftime('%Y/%m/%d')}/jornal/"
        f"caderno1_{publish_date.strftime('%Y-%m-%d')}.pdf"
    )
    
    response = requests.get(url, timeout=30)
    
    if response.status_code == 200:
        return response.content
    elif response.status_code == 404:
        raise ErrNotFound(f"PDF não encontrado para {publish_date}")
    else:
        raise requests.RequestException(
            f"Failed with unexpected status: {response.status_code}"
        )


def download_pages(publish_date: date) -> Tuple[List[Page], bytes]:
    """
    Baixa e extrai páginas do PDF do diário oficial.
    
    Args:
        publish_date: Data de publicação
        
    Returns:
        Tupla com (lista de páginas extraídas, bytes do PDF)
        
    Raises:
        ErrNotFound: Se o PDF não for encontrado
        requests.RequestException: Se houver erro na requisição
        RuntimeError: Se houver erro na extração
    """
    # Baixar PDF
    pdf_bytes = download_pdf(publish_date)
    
    # Extrair páginas
    extractor = PDFExtractor()
    pages = extractor.extract_pages(pdf_bytes)
    
    return pages, pdf_bytes

