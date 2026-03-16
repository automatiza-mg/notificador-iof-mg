"""Serviço para processamento do Diário Oficial."""

import logging
from datetime import date
from typing import Any

from flask import current_app
from redis import Redis
from rq import Queue

from app.iof.common import NotFoundError
from app.iof.v1.consulta import consulta_por_data, convert_pages
from app.repositories.document_interface import DocumentRepository
from app.services.search_service import SearchService

# Importar a função de notificação localmente para evitar ciclo de importação.
# Como notify.py importa SearchService, e SearchService é usado aqui,
# temos um potencial ciclo se importarmos notify_search_config no topo.

logger = logging.getLogger(__name__)


class GazetteService:
    """Serviço de domínio para orquestrar o processamento do diário."""

    def __init__(
        self,
        doc_repository: DocumentRepository,
        search_service: SearchService,
        queue_connection: Any | None = None,
    ) -> None:
        self.doc_repo = doc_repository
        self.search_service = search_service
        self.queue_connection = queue_connection

    def process_date(self, publish_date: date) -> None:
        """
        Baixa, processa e indexa o diário de uma data.

        1. Consulta API IOF
        2. Extrai texto do PDF
        3. Salva no Repositório de Documentos
        4. Enfileira notificações
        """
        logger.info("Iniciando processamento para %s", publish_date)

        try:
            # 1. Consultar API
            try:
                response = consulta_por_data(publish_date)
            except NotFoundError:
                logger.info("Nenhum diário encontrado para %s", publish_date)
                return

            # 2. Extrair Texto (Isso poderia ser um serviço separado PDFService)
            arquivo_b64 = response.dados.arquivo_caderno_principal.arquivo
            paginas_iof = convert_pages(arquivo_b64, publish_date)

            # Converter para formato do repositório (dict)
            pages_data = [
                {
                    "titulo": "",
                    "num_pagina": p.num_pagina,
                    "descricao": "",
                    "conteudo": p.conteudo,
                    "data_publicacao": p.data_publicacao,
                }
                for p in paginas_iof
            ]

            # 3. Salvar
            logger.info("Importando %d páginas...", len(pages_data))
            self.doc_repo.save_pages(pages_data)

            # 4. Notificar
            self._enqueue_notifications(publish_date)

        except Exception:
            logger.exception("Erro ao processar diário %s", publish_date)
            raise

    def _enqueue_notifications(self, publish_date: date) -> None:
        """Enfileira jobs de notificação para todas as configs ativas."""
        configs = self.search_service.list_configs(active_only=True)
        logger.info("Encontradas %d configurações ativas", len(configs))

        if not configs:
            return

        # Importar aqui para evitar ciclo se não for injetado
        from app.tasks.notify import notify_search_config  # noqa: PLC0415

        conn = self.queue_connection
        if not conn:
            # Fallback para conexão padrão (não ideal, mas prático)
            conn = Redis.from_url(
                current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
            )

        queue = Queue("default", connection=conn)

        for config in configs:
            queue.enqueue(
                notify_search_config,
                publish_date.isoformat(),
                config.id,
                job_timeout="10m",
            )
            logger.info("Job enfileirado para config %s", config.id)
