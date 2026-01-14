"""Worker para processar diário oficial diário."""
from datetime import date
from app import create_app
from app.extensions import db
from app.services.search_service import SearchService
from search.source import SearchSource, Pagina
from iof.v1.consulta import consulta_por_data, convert_pages
import os


def process_daily_gazette(publish_date: date) -> None:
    """
    Processa o diário oficial de uma data específica.
    
    Args:
        publish_date: Data de publicação do diário
    """
    app = create_app()
    with app.app_context():
        try:
            # Consultar diário via API v1
            try:
                response = consulta_por_data(publish_date)
            except Exception as e:
                if 'not found' in str(e).lower():
                    print(f"Nenhum diário encontrado para {publish_date}, pulando...")
                    return
                raise
            
            # Converter páginas do PDF
            arquivo = response.dados.arquivo_caderno_principal.arquivo
            paginas_iof = convert_pages(arquivo, publish_date)
            
            # Converter para Pagina do search
            paginas = [
                Pagina(
                    titulo="",
                    num_pagina=p.num_pagina,
                    descricao="",
                    conteudo=p.conteudo,
                    data_publicacao=p.data_publicacao
                )
                for p in paginas_iof
            ]
            
            # Importar páginas no banco de busca
            diarios_dir = app.config.get('DIARIOS_DIR', 'diarios')
            os.makedirs(diarios_dir, exist_ok=True)
            search_db = os.path.join(diarios_dir, 'diarios.db')
            source = SearchSource(search_db)
            
            try:
                print(f"Importando {len(paginas)} páginas...")
                source.import_pages(paginas)
                
                # Listar configurações ativas
                configs = SearchService.list_configs(active_only=True)
                print(f"Encontradas {len(configs)} configurações ativas")
                
                # Criar jobs de notificação para cada configuração
                from app.tasks.notify import notify_search_config
                from rq import Queue
                from redis import Redis
                
                redis_conn = Redis.from_url(
                    app.config.get('REDIS_URL', 'redis://localhost:6379/0')
                )
                queue = Queue('default', connection=redis_conn)
                
                for config in configs:
                    queue.enqueue(
                        notify_search_config,
                        publish_date.isoformat(),
                        config.id,
                        job_timeout='10m'
                    )
                    print(f"Job de notificação enfileirado para config {config.id}")
                    
            finally:
                source.close()
                
        except Exception as e:
            print(f"Erro ao processar diário: {e}")
            import traceback
            traceback.print_exc()
            raise

