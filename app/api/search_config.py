"""API para gerenciar configurações de busca."""
from datetime import date
from flask import Blueprint, request, jsonify, current_app
from app.services.search_service import SearchService
from app.utils.errors import not_found, validation_error, server_error
from search.source import SearchSource, Term, Trigger
from iof.v1.consulta import consulta_por_data, convert_pages

bp = Blueprint('search_config', __name__, url_prefix='/api/search/configs')


def config_to_dict(config):
    """Converte modelo SearchConfig para dicionário."""
    return {
        'id': config.id,
        'label': config.label,
        'description': config.description,
        'attach_csv': config.attach_csv,
        'mail_to': config.mail_to,
        'mail_subject': config.mail_subject,
        'teams_webhook': config.teams_webhook,
        'active': config.active,
        'created_at': config.created_at.isoformat() if config.created_at else None,
        'updated_at': config.updated_at.isoformat() if config.updated_at else None,
        'terms': [
            {
                'term': term.term,
                'exact': term.exact
            }
            for term in config.terms
        ]
    }


@bp.route('', methods=['GET'])
def list_configs():
    """Lista todas as configurações de busca."""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        configs = SearchService.list_configs(active_only=active_only)
        return jsonify([config_to_dict(c) for c in configs]), 200
    except Exception as e:
        return server_error(str(e))


@bp.route('', methods=['POST'])
def create_config():
    """Cria uma nova configuração de busca."""
    try:
        data = request.get_json()
        if not data:
            return validation_error({'body': 'JSON inválido ou vazio'})
        
        # Validação básica
        errors = {}
        if not data.get('label'):
            errors['label'] = 'Deve ser preenchido'
        if 'terms' in data and len(data['terms']) > 5:
            errors['terms'] = 'Deve possuir no máximo 5 items'
        
        if errors:
            return validation_error(errors)
        
        config = SearchService.save_config(data)
        return jsonify(config_to_dict(config)), 201
    except Exception as e:
        return server_error(str(e))


@bp.route('/<int:config_id>', methods=['GET'])
def get_config(config_id):
    """Busca uma configuração por ID."""
    try:
        config = SearchService.get_config(config_id)
        if not config:
            return not_found()
        return jsonify(config_to_dict(config)), 200
    except Exception as e:
        return server_error(str(e))


@bp.route('/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    """Atualiza uma configuração de busca."""
    try:
        data = request.get_json()
        if not data:
            return validation_error({'body': 'JSON inválido ou vazio'})
        
        # Validação básica
        errors = {}
        if 'label' in data and not data.get('label'):
            errors['label'] = 'Não pode ser vazio'
        if 'terms' in data and len(data['terms']) > 5:
            errors['terms'] = 'Deve possuir no máximo 5 items'
        
        if errors:
            return validation_error(errors)
        
        config = SearchService.update_config(config_id, data)
        if not config:
            return not_found()
        return jsonify(config_to_dict(config)), 200
    except Exception as e:
        return server_error(str(e))


@bp.route('/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    """Deleta uma configuração de busca."""
    try:
        deleted = SearchService.delete_config(config_id)
        if not deleted:
            return not_found()
        return '', 204
    except Exception as e:
        return server_error(str(e))


@bp.route('/<int:config_id>/backtest', methods=['GET'])
def backtest_config(config_id):
    """Executa backtest de uma configuração para uma data específica."""
    try:
        # Verificar se backtest está habilitado
        import os
        app_env = os.getenv('APP_ENV', 'development')
        if app_env != 'development':
            return not_found("Backtest disponível apenas em desenvolvimento")
        
        # Buscar configuração
        config = SearchService.get_config(config_id)
        if not config:
            return not_found()
        
        # Obter data do query string
        date_str = request.args.get('date')
        if not date_str:
            return validation_error({'date': 'Parâmetro date é obrigatório'})
        
        try:
            test_date = date.fromisoformat(date_str)
        except ValueError:
            return validation_error({'date': 'Data deve estar no formato YYYY-MM-DD'})
        
        if test_date > date.today():
            return validation_error({'date': 'Não pode ser uma data futura'})
        
        # Inicializar source de busca
        diarios_dir = current_app.config.get('DIARIOS_DIR', 'diarios')
        import os
        os.makedirs(diarios_dir, exist_ok=True)
        search_db = os.path.join(diarios_dir, 'diarios.db')
        source = SearchSource(search_db)
        
        try:
            # Verificar se já tem páginas importadas
            has_pages = source.has_pages(test_date)
            
            if not has_pages:
                # Baixar e importar diário
                try:
                    response = consulta_por_data(test_date)
                    arquivo = response.dados.arquivo_caderno_principal.arquivo
                    paginas_iof = convert_pages(arquivo, test_date)
                    # Converter para Pagina do search
                    from search.source import Pagina as SearchPagina
                    paginas = [
                        SearchPagina(
                            titulo="",
                            num_pagina=p.num_pagina,
                            descricao="",
                            conteudo=p.conteudo,
                            data_publicacao=p.data_publicacao
                        )
                        for p in paginas_iof
                    ]
                    source.import_pages(paginas)
                except Exception as e:
                    source.close()
                    if 'not found' in str(e).lower() or '404' in str(e):
                        return not_found(f"Diário não encontrado para {test_date}")
                    return server_error(f"Erro ao baixar diário: {str(e)}")
            
            # Converter termos da config para Term do search
            search_terms = [
                Term(term=term.term, exact=term.exact)
                for term in config.terms
            ]
            
            # Executar busca
            report = source.lookup(Trigger.BACKTEST, test_date, search_terms)
            
            # Converter report para JSON
            result = {
                'publish_date': report.publish_date.isoformat(),
                'highlights': [
                    {
                        'page': h.page,
                        'content': h.content,
                        'term': h.term,
                        'page_url': h.page_url
                    }
                    for h in report.highlights
                ],
                'search_terms': [
                    {
                        'term': t.term,
                        'exact': t.exact
                    }
                    for t in report.search_terms
                ],
                'trigger': report.trigger.value,
                'count': report.count
            }
            
            return jsonify(result), 200
            
        finally:
            source.close()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return server_error(str(e))

