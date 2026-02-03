"""Serviço para processamento do Diário Oficial."""

import os
import logging
from datetime import date
from typing import List, Optional
from flask import current_app
from rq import Queue
from redis import Redis

from app.repositories.document_interface import DocumentRepository
from app.services.search_service import SearchService
from app.iof.v1.consulta import consulta_por_data, convert_pages, ErrNotFound
# Importar a função de notificação apenas onde necessário para evitar ciclo de importação
# ou reestruturar notify.py para não depender de app.services.search_service no topo se possível.
# Como notify.py importa SearchService, e SearchService é usado aqui, temos um potencial ciclo
# se importarmos notify_search_config no topo. Vamos manter o import local para essa função específica.

logger = logging.getLogger(__name__)


class GazetteService:
    """Serviço de domínio para orquestrar o processamento do diário."""

    def __init__(
        self,
        doc_repository: DocumentRepository,
        search_service: SearchService,
        queue_connection=None,
    ):
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
        logger.info(f"Iniciando processamento para {publish_date}")

        try:
            # 1. Consultar API
            try:
                response = consulta_por_data(publish_date)
            except ErrNotFound:
                logger.info(f"Nenhum diário encontrado para {publish_date}")
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
            logger.info(f"Importando {len(pages_data)} páginas...")
            self.doc_repo.save_pages(pages_data)

            # 4. Notificar
            self._enqueue_notifications(publish_date)

        except Exception as e:
            logger.error(f"Erro ao processar diário {publish_date}: {e}", exc_info=True)
            raise

    def _enqueue_notifications(self, publish_date: date):
        """Enfileira jobs de notificação para todas as configs ativas."""
        configs = self.search_service.list_configs(active_only=True)
        logger.info(f"Encontradas {len(configs)} configurações ativas")

        if not configs:
            return

        # Importar aqui para evitar ciclo se não for injetado
        from app.tasks.notify import notify_search_config

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
            logger.info(f"Job enfileirado para config {config.id}")
