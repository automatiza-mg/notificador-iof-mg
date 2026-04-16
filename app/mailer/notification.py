"""Geração de emails de notificação."""

import urllib.parse
from dataclasses import dataclass
from datetime import date

from jinja2 import Template

from app.mailer.csv_generator import generate_csv_from_report, get_csv_filename
from app.mailer.message import Attachment, Email
from app.mailer.unsubscribe import (
    build_unsubscribe_url,
    generate_unsubscribe_token,
    resolve_app_base_url,
)
from app.models.search_config import SearchConfig
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

Foram encontradas {{ count }} novas notificações para o Diário Oficial do dia \
{{ publish_date }} para os termos:
{% for term in search_terms %}
- {{ term.term }}
{% endfor %}

Os trechos destacados são:
{% for highlight in highlights %}
- Página {{ highlight.page }}: {{ highlight.content }}
{% endfor %}

{% if unsubscribe_url %}
Você está recebendo este email porque foi cadastrado no alerta "{{ alert_label }}".
Não deseja mais receber este alerta? Descadastre este email: {{ unsubscribe_url }}
{% endif %}
"""


@dataclass(frozen=True, slots=True)
class NotificationEmailContext:
    """Contexto para montar email de notificação individual."""

    recipient: str
    unsubscribe_url: str


def build_notification_email_context(
    *,
    config: SearchConfig,
    recipient: str,
    secret_key: str,
    app_base_url: str,
    app_env: str,
) -> NotificationEmailContext:
    """Cria contexto individual de descadastro para um destinatário."""
    resolved_base_url = resolve_app_base_url(
        configured_base_url=app_base_url,
        app_env=app_env,
    )
    token = generate_unsubscribe_token(
        config_id=config.id,
        email=recipient,
        secret_key=secret_key,
    )
    unsubscribe_url = build_unsubscribe_url(
        app_base_url=resolved_base_url,
        token=token,
    )
    return NotificationEmailContext(
        recipient=recipient,
        unsubscribe_url=unsubscribe_url,
    )


def build_notification_emails(
    *,
    config: SearchConfig,
    report: Report,
    secret_key: str,
    app_base_url: str,
    app_env: str,
) -> list[Email]:
    """Cria uma mensagem individual para cada destinatário do alerta."""
    emails: list[Email] = []
    subject = config.mail_subject or "Novas notificações - Diário Oficial"

    for recipient in config.mail_to:
        context = build_notification_email_context(
            config=config,
            recipient=recipient,
            secret_key=secret_key,
            app_base_url=app_base_url,
            app_env=app_env,
        )
        emails.append(
            notification_email(
                [context.recipient],
                report,
                subject=subject,
                attach_csv=config.attach_csv,
                alert_label=config.label,
                unsubscribe_url=context.unsubscribe_url,
            )
        )

    return emails


def notification_email(
    to: list[str],
    report: Report,
    *,
    subject: str | None = None,
    attach_csv: bool = False,
    alert_label: str = "Alerta do Diário Oficial",
    unsubscribe_url: str | None = None,
) -> Email:
    """
    Gera email de notificação a partir de um relatório de busca.

    Args:
        to: Lista de endereços de email
        report: Relatório de busca
        subject: Assunto do email (opcional)
        attach_csv: Se True, anexa arquivo CSV com os resultados
        alert_label: Nome do alerta usado no rodapé do email
        unsubscribe_url: URL de descadastro individual

    Returns:
        Email pronto para envio
    """
    # Gerar link do jornal do dia
    gazette_link = generate_daily_gazette_link(report.publish_date)
    publish_date_formatted = report.publish_date.strftime("%d/%m/%Y")

    template = Template(NOTIFICATION_TEMPLATE)

    # Preparar dados para template
    template_data = {
        "alert_label": alert_label,
        "count": report.count,
        "publish_date": publish_date_formatted,
        "gazette_link": gazette_link,
        "search_terms": [{"term": t.term} for t in report.search_terms],
        "highlights": [
            {"page": h.page, "content": h.content} for h in report.highlights
        ],
        "unsubscribe_url": unsubscribe_url or "",
    }

    text_body = template.render(**template_data)

    # Gerar HTML básico
    html_body = f"""
    <html>
    <body>
        <h2>Novas notificações - Diário Oficial</h2>
        <p style="margin-bottom: 20px;">
            <a href="{gazette_link}" style="background-color: #007bff; color: white; \
padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Acessar Diário Oficial de {publish_date_formatted}
            </a>
        </p>
        <p>Foram encontradas {report.count} novas notificações para o Diário Oficial \
do dia {publish_date_formatted} para os termos:</p>
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
        <hr style="margin: 32px 0; border: 0; border-top: 1px solid #E5E7EB;">
    """
    if unsubscribe_url:
        html_body += f"""
        <p style="font-size: 14px; color: #4B5563; line-height: 1.6;">
            Você está recebendo este email porque foi cadastrado no alerta
            <strong>{alert_label}</strong>.<br>
            <a href="{unsubscribe_url}"
               style="color: #2563EB; text-decoration: underline;">
                Descadastrar e-mail
            </a>
        </p>
        """
    html_body += """
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
