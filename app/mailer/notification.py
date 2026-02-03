"""Geração de emails de notificação."""

import urllib.parse
from datetime import date
from typing import List, Optional
from jinja2 import Template
from app.mailer.mailer import Email, Attachment
from app.mailer.csv_generator import generate_csv_from_report, get_csv_filename
from app.search.source import Report


def generate_daily_gazette_link(target_date: date) -> str:
    """
    Gera o link profundo para uma data específica do Diário Oficial.

    O link utiliza o formato com parâmetro ?dados= contendo um JSON codificado
    que carrega o estado da aplicação diretamente na edição do dia.

    Args:
        target_date: Data de publicação do jornal

    Returns:
        URL do jornal do dia no formato: https://www.jornalminasgerais.mg.gov.br/edicao-do-dia?dados=...
    """
    date_str = target_date.strftime("%Y-%m-%d")
    json_payload = f'{{"dataPublicacaoSelecionada":"{date_str}T03:00:00.000Z"}}'

    # Codificação segura para URL
    encoded_payload = urllib.parse.quote(json_payload)
    base_url = "https://www.jornalminasgerais.mg.gov.br/edicao-do-dia?dados="

    return base_url + encoded_payload


NOTIFICATION_TEMPLATE = """
Acessar Diário Oficial de {{ publish_date }}: {{ gazette_link }}

Foram encontradas {{ count }} novas notificações para o Diário Oficial do dia {{ publish_date }} para os termos:
{% for term in search_terms %}
- {{ term.term }}
{% endfor %}

Os trechos destacados são:
{% for highlight in highlights %}
- Página {{ highlight.page }}: {{ highlight.content }}
{% endfor %}
"""


def notification_email(
    to: List[str], report: Report, subject: str = None, attach_csv: bool = False
) -> Email:
    """
    Gera email de notificação a partir de um relatório de busca.

    Args:
        to: Lista de endereços de email
        report: Relatório de busca
        subject: Assunto do email (opcional)
        attach_csv: Se True, anexa arquivo CSV com os resultados

    Returns:
        Email pronto para envio
    """
    # Gerar link do jornal do dia
    gazette_link = generate_daily_gazette_link(report.publish_date)
    publish_date_formatted = report.publish_date.strftime("%d/%m/%Y")

    template = Template(NOTIFICATION_TEMPLATE)

    # Preparar dados para template
    template_data = {
        "count": report.count,
        "publish_date": publish_date_formatted,
        "gazette_link": gazette_link,
        "search_terms": [{"term": t.term} for t in report.search_terms],
        "highlights": [
            {"page": h.page, "content": h.content} for h in report.highlights
        ],
    }

    text_body = template.render(**template_data)

    # Gerar HTML básico
    html_body = f"""
    <html>
    <body>
        <h2>Novas notificações - Diário Oficial</h2>
        <p style="margin-bottom: 20px;">
            <a href="{gazette_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Acessar Diário Oficial de {publish_date_formatted}
            </a>
        </p>
        <p>Foram encontradas {report.count} novas notificações para o Diário Oficial do dia {publish_date_formatted} para os termos:</p>
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
            {highlight.content}
        </li>
        """
    html_body += """
        </ul>
    </body>
    </html>
    """

    # Gerar anexo CSV se solicitado
    attachments = None
    if attach_csv and report.count > 0:
        csv_content = generate_csv_from_report(report)
        csv_filename = get_csv_filename(report)
        attachments = [
            Attachment(
                filename=csv_filename,
                content=csv_content,
                content_type="text/csv; charset=utf-8",
            )
        ]

    return Email(
        to=to,
        subject=subject or "Novas notificações - Diário Oficial",
        text=text_body,
        html=html_body,
        attachments=attachments,
    )
