"""Implementação SQLite do DocumentRepository."""

import sqlite3
import json
from datetime import date
from typing import List
from pathlib import Path
from urllib.parse import quote
from app.repositories.document_interface import (
    DocumentRepository,
    SearchReport,
    SearchResult,
)


class SQLiteDocumentRepository(DocumentRepository):
    """Implementação usando SQLite FTS5."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inicializa banco e schema se necessário."""
        # Garantir que o diretório pai existe
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = self._get_conn()
        try:
            # Carregar schema do arquivo original (mantendo compatibilidade)
            schema_path = Path(__file__).parent.parent / "search" / "schema.sql"
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())
            conn.commit()
        finally:
            conn.close()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def save_pages(self, pages: List[dict]) -> None:
        """
        Salva páginas. Espera dict com: titulo, num_pagina, descricao, conteudo, data_publicacao.
        """
        conn = self._get_conn()
        try:
            query = """
            REPLACE INTO documentos (titulo, num_pagina, descricao, conteudo, data_publicacao)
            VALUES (?, ?, ?, ?, ?)
            """
            for p in pages:
                conn.execute(
                    query,
                    (
                        p.get("titulo", ""),
                        p["num_pagina"],
                        p.get("descricao", ""),
                        p["conteudo"],
                        p["data_publicacao"].strftime("%Y-%m-%d"),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def search(self, publish_date: date, terms: List[dict]) -> SearchReport:
        """
        Busca termos. Espera lista de dict com 'term' e 'exact'.
        """
        conn = self._get_conn()
        results = []
        date_str = publish_date.strftime("%Y-%m-%d")

        try:
            for term_data in terms:
                term = term_data["term"]
                if term_data.get("exact"):
                    search_term = f'"{term}"'
                else:
                    search_term = term

                query = """
                SELECT
                    doc.num_pagina,
                    snippet(documentos_fts, 0, '<b>', '</b>', '...', 32) AS trecho
                FROM documentos_fts doc_fts
                INNER JOIN documentos doc ON doc_fts.rowid = doc.id
                WHERE doc.data_publicacao = ?
                AND documentos_fts MATCH ?
                """

                cursor = conn.execute(query, (date_str, search_term))
                for row in cursor:
                    results.append(
                        SearchResult(
                            page=row["num_pagina"],
                            content=row["trecho"],
                            term=term,
                            page_url=self._generate_url(
                                publish_date, row["num_pagina"]
                            ),
                        )
                    )

            return SearchReport(
                publish_date=publish_date, results=results, count=len(results)
            )
        finally:
            conn.close()

    def has_content(self, publish_date: date) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT count(*) FROM documentos WHERE data_publicacao = ?",
                (publish_date.strftime("%Y-%m-%d"),),
            )
            return cursor.fetchone()[0] > 0
        finally:
            conn.close()

    def _generate_url(self, publish_date: date, page_num: int) -> str:
        # Lógica duplicada de source.py, idealmente mover para utils
        date_str = publish_date.strftime("%Y-%m-%d")
        payload = {
            "dataPublicacao": f"{date_str}T03:00:00.000Z",
            "idCadernoEdicaoSelecionado": 326074,
            "paginaSelecionada": page_num,
        }
        json_payload = json.dumps(payload, separators=(",", ":"))
        return "https://www.jornalminasgerais.mg.gov.br/edicao-do-dia?dados=" + quote(
            json_payload
        )
