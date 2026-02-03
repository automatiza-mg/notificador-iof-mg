"""Extração de texto de PDFs usando poppler-utils."""
import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List


@dataclass
class Page:
    """Representa uma página extraída de um PDF."""
    number: int
    content: str


class PDFExtractor:
    """Extrator de texto de PDFs usando poppler-utils."""
    
    PDFINFO = "pdfinfo"
    PDFTOTEXT = "pdftotext"
    PAGES_PREFIX = "Pages:"
    
    def extract_pages_from_path(self, path: str) -> List[Page]:
        """
        Extrai texto de todas as páginas de um PDF a partir do caminho do arquivo.
        
        Args:
            path: Caminho para o arquivo PDF
            
        Returns:
            Lista de páginas extraídas
            
        Raises:
            FileNotFoundError: Se o arquivo não existir
            subprocess.CalledProcessError: Se pdfinfo ou pdftotext falharem
            ValueError: Se não conseguir determinar o número de páginas
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        
        # Obter número de páginas
        try:
            result = subprocess.run(
                [self.PDFINFO, path],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"{self.PDFINFO} falhou: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError(
                f"{self.PDFINFO} não encontrado. "
                "Instale poppler-utils (brew install poppler ou apt-get install poppler-utils)"
            ) from None
        
        # Parsear número de páginas
        num_pages = 0
        for line in result.stdout.split('\n'):
            if line.startswith(self.PAGES_PREFIX):
                parts = line.split()
                if len(parts) == 2:
                    try:
                        num_pages = int(parts[1])
                    except ValueError:
                        raise ValueError(f"Não foi possível parsear número de páginas: {line}")
                break
        
        if num_pages == 0:
            raise ValueError("Não foi possível determinar o número de páginas do PDF")
        
        # Extrair cada página
        pages = []
        for page_num in range(1, num_pages + 1):
            try:
                result = subprocess.run(
                    [
                        self.PDFTOTEXT,
                        "-f", str(page_num),
                        "-l", str(page_num),
                        path,
                        "-"  # Output para stdout
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Falha ao extrair página {page_num}: {e.stderr}") from e
            except FileNotFoundError:
                raise RuntimeError(
                    f"{self.PDFTOTEXT} não encontrado. "
                    "Instale poppler-utils (brew install poppler ou apt-get install poppler-utils)"
                ) from None
            
            pages.append(Page(
                number=page_num,
                content=result.stdout
            ))
        
        return pages
    
    def extract_pages(self, content: bytes) -> List[Page]:
        """
        Extrai texto de todas as páginas de um PDF a partir do conteúdo em bytes.
        
        Args:
            content: Conteúdo do PDF em bytes
            
        Returns:
            Lista de páginas extraídas
            
        Raises:
            subprocess.CalledProcessError: Se pdfinfo ou pdftotext falharem
            ValueError: Se não conseguir determinar o número de páginas
        """
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp:
            try:
                tmp.write(content)
                tmp_path = tmp.name
            except Exception as e:
                os.unlink(tmp_path)
                raise RuntimeError(f"Falha ao escrever arquivo temporário: {e}") from e
        
        try:
            # Extrair páginas
            pages = self.extract_pages_from_path(tmp_path)
        finally:
            # Limpar arquivo temporário
            try:
                os.unlink(tmp_path)
            except OSError:
                pass  # Ignorar erros ao deletar arquivo temporário
        
        return pages

