"""Extração de texto de PDFs usando poppler-utils."""

import contextlib
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


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

    def extract_pages_from_path(self, path: str) -> list[Page]:
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
        if not Path(path).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        # Obter número de páginas
        try:
            result = subprocess.run(  # noqa: S603
                [self.PDFINFO, path], capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"{self.PDFINFO} falhou: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError(
                f"{self.PDFINFO} não encontrado. "
                "Instale poppler-utils (ex: brew install poppler)"
            ) from None

        # Parsear número de páginas
        num_pages = 0
        for line in result.stdout.split("\n"):
            if line.startswith(self.PAGES_PREFIX):
                parts = line.split()
                if len(parts) == 2:
                    try:
                        num_pages = int(parts[1])
                    except ValueError as e:
                        raise ValueError(
                            f"Não foi possível parsear número de páginas: {line}"
                        ) from e
                break

        if num_pages == 0:
            raise ValueError("Não foi possível determinar o número de páginas do PDF")

        # Extrair cada página
        pages = []
        for page_num in range(1, num_pages + 1):
            try:
                result = subprocess.run(  # noqa: S603
                    [
                        self.PDFTOTEXT,
                        "-f",
                        str(page_num),
                        "-l",
                        str(page_num),
                        path,
                        "-",  # Output para stdout
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"Falha ao extrair página {page_num}: {e.stderr}"
                ) from e
            except FileNotFoundError:
                raise RuntimeError(
                    f"{self.PDFTOTEXT} não encontrado. "
                    "Instale poppler-utils (ex: brew install poppler)"
                ) from None

            pages.append(Page(number=page_num, content=result.stdout))

        return pages

    def extract_pages(self, content: bytes) -> list[Page]:
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
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
            try:
                tmp.write(content)
            except Exception as e:
                Path(tmp_path).unlink(missing_ok=True)
                raise RuntimeError(f"Falha ao escrever arquivo temporário: {e}") from e

        try:
            # Extrair páginas
            pages = self.extract_pages_from_path(tmp_path)
        finally:
            # Limpar arquivo temporário
            with contextlib.suppress(OSError):
                Path(tmp_path).unlink()

        return pages
