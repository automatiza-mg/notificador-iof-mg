"""Geração de emails de notificação."""
from typing import List
from jinja2 import Template
from mailer.mailer import Email
from search.source import Report


NOTIFICATION_TEMPLATE = """
Foram encontradas {{ count }} novas notificações para o Diário Oficial do dia {{ publish_date }} para os termos:
{% for term in search_terms %}
- {{ term.term }}
{% endfor %}

Os trechos destacados são:
{% for highlight in highlights %}
- Página {{ highlight.page }}: {{ highlight.content }}
  URL: {{ highlight.page_url }}
{% endfor %}
"""


def notification_email(to: List[str], report: Report, subject: str = None) -> Email:
    """
    Gera email de notificação a partir de um relatório de busca.
    
    Args:
        to: Lista de endereços de email
        report: Relatório de busca
        subject: Assunto do email (opcional)
        
    Returns:
        Email pronto para envio
    """
    template = Template(NOTIFICATION_TEMPLATE)
    
    # Preparar dados para template
    template_data = {
        'count': report.count,
        'publish_date': report.publish_date.strftime('%d/%m/%Y'),
        'search_terms': [
            {'term': t.term}
            for t in report.search_terms
        ],
        'highlights': [
            {
                'page': h.page,
                'content': h.content,
                'page_url': h.page_url
            }
            for h in report.highlights
        ]
    }
    
    text_body = template.render(**template_data)
    
    # Gerar HTML básico
    html_body = f"""
    <html>
    <body>
        <h2>Novas notificações - Diário Oficial</h2>
        <p>Foram encontradas {report.count} novas notificações para o Diário Oficial do dia {report.publish_date.strftime('%d/%m/%Y')} para os termos:</p>
        <ul>
    """
    for term in report.search_terms:
        html_body += f"<li>{term.term}</li>"
    html_body += """
        </ul>
        <h3>Os trechos destacados são:</h3>
        <ul>
    """
    for highlight in report.highlights:
        html_body += f"""
        <li>
            <strong>Página {highlight.page}:</strong><br>
            {highlight.content}<br>
            <a href="{highlight.page_url}">Ver página</a>
        </li>
        """
    html_body += """
        </ul>
    </body>
    </html>
    """
    
    return Email(
        to=to,
        subject=subject or "Novas notificações - Diário Oficial",
        text=text_body,
        html=html_body
    )

