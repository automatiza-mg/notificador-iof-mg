"""Serviço para gerenciar configurações de busca."""
from typing import List, Optional
from app.extensions import db
from app.models.search_config import SearchConfig, SearchTerm


class SearchService:
    """Serviço para operações CRUD de configurações de busca."""
    
    @staticmethod
    def save_config(config_data: dict) -> SearchConfig:
        """
        Salva uma nova configuração de busca.
        
        Args:
            config_data: Dicionário com dados da configuração:
                - label: str
                - description: str (opcional)
                - attach_csv: bool
                - mail_to: List[str]
                - mail_subject: str (opcional)
                - teams_webhook: str (opcional)
                - terms: List[dict] com 'term' e 'exact'
        
        Returns:
            Configuração salva
        """
        config = SearchConfig(
            label=config_data['label'],
            description=config_data.get('description', ''),
            attach_csv=config_data.get('attach_csv', False),
            mail_to=config_data.get('mail_to', []),
            mail_subject=config_data.get('mail_subject', ''),
            teams_webhook=config_data.get('teams_webhook'),
            active=config_data.get('active', True)
        )
        
        db.session.add(config)
        db.session.flush()  # Para obter o ID
        
        # Adicionar termos
        for term_data in config_data.get('terms', []):
            term = SearchTerm(
                term=term_data['term'],
                exact=term_data.get('exact', True),
                search_config_id=config.id
            )
            db.session.add(term)
        
        db.session.commit()
        db.session.refresh(config)
        return config
    
    @staticmethod
    def get_config(config_id: int) -> Optional[SearchConfig]:
        """
        Busca uma configuração por ID.
        
        Args:
            config_id: ID da configuração
            
        Returns:
            Configuração encontrada ou None
        """
        return SearchConfig.query.get(config_id)
    
    @staticmethod
    def list_configs(active_only: bool = True) -> List[SearchConfig]:
        """
        Lista todas as configurações.
        
        Args:
            active_only: Se True, retorna apenas configurações ativas
            
        Returns:
            Lista de configurações
        """
        query = SearchConfig.query
        if active_only:
            query = query.filter(SearchConfig.active == True)
        return query.all()
    
    @staticmethod
    def update_config(config_id: int, config_data: dict) -> Optional[SearchConfig]:
        """
        Atualiza uma configuração existente.
        
        Args:
            config_id: ID da configuração
            config_data: Dicionário com dados atualizados
            
        Returns:
            Configuração atualizada ou None se não encontrada
        """
        config = SearchConfig.query.get(config_id)
        if not config:
            return None
        
        # Atualizar campos
        if 'label' in config_data:
            config.label = config_data['label']
        if 'description' in config_data:
            config.description = config_data['description']
        if 'attach_csv' in config_data:
            config.attach_csv = config_data['attach_csv']
        if 'mail_to' in config_data:
            config.mail_to = config_data['mail_to']
        if 'mail_subject' in config_data:
            config.mail_subject = config_data['mail_subject']
        if 'teams_webhook' in config_data:
            config.teams_webhook = config_data['teams_webhook']
        if 'active' in config_data:
            config.active = config_data['active']
        
        # Remover termos antigos
        SearchTerm.query.filter_by(search_config_id=config_id).delete()
        
        # Adicionar novos termos
        for term_data in config_data.get('terms', []):
            term = SearchTerm(
                term=term_data['term'],
                exact=term_data.get('exact', True),
                search_config_id=config.id
            )
            db.session.add(term)
        
        db.session.commit()
        db.session.refresh(config)
        return config
    
    @staticmethod
    def delete_config(config_id: int) -> bool:
        """
        Deleta uma configuração.
        
        Args:
            config_id: ID da configuração
            
        Returns:
            True se deletada, False se não encontrada
        """
        config = SearchConfig.query.get(config_id)
        if not config:
            return False
        
        db.session.delete(config)
        db.session.commit()
        return True

