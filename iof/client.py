"""Cliente para API do Diário Oficial de MG."""
import requests
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional
from urllib.parse import urlencode


BASE_URL = "https://www.jornalminasgerais.mg.gov.br/api/beta"


class ErrNotFound(Exception):
    """Erro quando diário não é encontrado."""
    pass


@dataclass
class Pagina:
    """Página do Diário Oficial."""
    titulo: str
    num_pagina: int
    descricao: str
    conteudo: str
    data_publicacao: date


class IOFClient:
    """Cliente para API do Diário Oficial."""
    
    def __init__(self, username: str, password: str):
        """
        Inicializa o cliente.
        
        Args:
            username: Usuário para autenticação básica
            password: Senha para autenticação básica
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.timeout = 5
    
    def get_latest(self) -> List[Pagina]:
        """
        Busca o diário mais recente.
        
        Returns:
            Lista de páginas do diário
            
        Raises:
            ErrNotFound: Se não houver diário disponível
            requests.RequestException: Se houver erro na requisição
        """
        url = f"{BASE_URL}/jornal"
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                raise ErrNotFound("Nenhum diário encontrado")
            
            paginas = []
            for item in data:
                # Parsear data
                data_pub = self._parse_date(item.get('dataPublicacao', ''))
                
                paginas.append(Pagina(
                    titulo=item.get('titulo', ''),
                    num_pagina=item.get('pagina', 0),
                    descricao=item.get('descricao', ''),
                    conteudo=item.get('conteudo', ''),
                    data_publicacao=data_pub
                ))
            
            return paginas
        else:
            raise requests.RequestException(f"Request failed with status {response.status_code}")
    
    def get_by_date(self, publish_date: date) -> List[Pagina]:
        """
        Busca diário por data.
        
        Args:
            publish_date: Data de publicação
            
        Returns:
            Lista de páginas do diário
            
        Raises:
            ErrNotFound: Se não houver diário para a data
            requests.RequestException: Se houver erro na requisição
        """
        # Formato: DDMMYYYY
        date_str = publish_date.strftime('%d%m%Y')
        url = f"{BASE_URL}/jornal?data={date_str}"
        
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                raise ErrNotFound(f"Nenhum diário encontrado para {publish_date}")
            
            paginas = []
            for item in data:
                data_pub = self._parse_date(item.get('dataPublicacao', ''))
                
                paginas.append(Pagina(
                    titulo=item.get('titulo', ''),
                    num_pagina=item.get('pagina', 0),
                    descricao=item.get('descricao', ''),
                    conteudo=item.get('conteudo', ''),
                    data_publicacao=data_pub
                ))
            
            return paginas
        else:
            raise requests.RequestException(f"Request failed with status {response.status_code}")
    
    def _parse_date(self, date_str: str) -> date:
        """
        Parseia string de data para date.
        
        Args:
            date_str: String de data (formato: YYYY-MM-DDTHH:MM:SS ou YYYY-MM-DD)
            
        Returns:
            Objeto date
        """
        if not date_str:
            return date.today()
        
        try:
            # Tentar formato com hora
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
            return dt.date()
        except ValueError:
            try:
                # Tentar formato apenas data
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return date.today()

