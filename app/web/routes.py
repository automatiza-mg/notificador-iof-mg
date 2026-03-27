"""Rotas web para interface HTML."""

import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from pydantic import ValidationError

from app.iof.v1.consulta import consulta_por_data, convert_pages
from app.mailer.mailer import Mailer
from app.mailer.notification import notification_email
from app.repositories.search_config_repository import SearchConfigRepository
from app.schemas.search_config import SearchConfigCreate, SearchConfigUpdate
from app.search.source import Pagina as SearchPagina
from app.search.source import SearchSource, Term, Trigger
from app.services.search_service import SearchService

bp = Blueprint("web", __name__)


# Helper para instanciar serviço
def get_service() -> SearchService:
    repository = SearchConfigRepository()
    return SearchService(repository)


@bp.route("/")
@login_required
def index() -> Any:
    """Lista todas as configurações do usuário logado."""
    active_only = request.args.get("active_only", "false").lower() == "true"
    page = request.args.get("page", 1, type=int)
    service = get_service()
    configs_pagination = service.list_configs_paginated(
        page=page, per_page=6, active_only=active_only, user_id=current_user.id
    )
    return render_template(
        "index.html", configs=configs_pagination, active_only=active_only
    )


@bp.route("/configs/new", methods=["GET", "POST"])
@login_required
def create_config() -> Any:
    """Criar nova configuração."""
    if request.method == "POST":
        data = request.form.to_dict()

        # Processar termos
        terms = []
        term_inputs = request.form.getlist("term")
        exact_inputs = request.form.getlist("term_exact")

        for i, term_text in enumerate(term_inputs):
            if term_text.strip():
                terms.append(
                    {
                        "term": term_text.strip(),
                        "exact": exact_inputs[i] == "on"
                        if i < len(exact_inputs)
                        else True,
                    }
                )

        # Processar emails
        mail_to = [
            email.strip() for email in request.form.getlist("mail_to") if email.strip()
        ]

        # Montar dados da configuração
        config_data = {
            "label": data.get("label", "").strip(),
            "description": data.get("description", "").strip(),
            "attach_csv": data.get("attach_csv") == "on",
            "mail_to": mail_to,
            "mail_subject": data.get("mail_subject", "").strip(),
            "teams_webhook": None,  # Teams removido da interface
            "terms": terms,
            "active": True,
        }

        try:
            # Validar com Pydantic
            config_create = SearchConfigCreate.model_validate(config_data)
            service = get_service()
            service.save_config(config_create, user_id=current_user.id)

            flash("Configuração criada com sucesso!", "success")
            return redirect(url_for("web.index"))

        except ValidationError as e:
            # Mapear erros do Pydantic para o template
            errors = {}
            for err in e.errors():
                loc = err["loc"]
                field = loc[0] if loc else "geral"
                msg = err["msg"]
                # Simplificar mensagens para usuário final
                if field == "terms":
                    msg = "Verifique os termos de busca (mínimo 1, máximo 5)"
                elif field == "mail_to":
                    msg = "Verifique os emails (máximo 5) e se são válidos"
                elif field == "label":
                    msg = "Nome é obrigatório"
                errors[str(field)] = msg

            return render_template("create.html", errors=errors, form_data=config_data)

        except Exception as e:  # noqa: BLE001  # noqa: BLE001  # noqa: BLE001
            flash(f"Erro ao criar configuração: {e!s}", "error")
            return render_template("create.html", errors={}, form_data=config_data)

    return render_template("create.html", errors={}, form_data={})


@bp.route("/configs/<int:config_id>")
@login_required
def detail_config(config_id: int) -> Any:
    """Visualizar detalhes de uma configuração (apenas do dono)."""
    service = get_service()
    config = service.get_config(config_id, user_id=current_user.id)
    if not config:
        flash("Configuração não encontrada", "error")
        return redirect(url_for("web.index"))

    return render_template("detail.html", config=config)


@bp.route("/configs/<int:config_id>/edit", methods=["GET", "POST"])
@login_required
def edit_config(config_id: int) -> Any:
    """Editar configuração (apenas do dono)."""
    service = get_service()
    config = service.get_config(config_id, user_id=current_user.id)
    if not config:
        flash("Configuração não encontrada", "error")
        return redirect(url_for("web.index"))

    if request.method == "POST":
        data = request.form.to_dict()

        # Processar termos
        terms = []
        term_inputs = request.form.getlist("term")
        exact_inputs = request.form.getlist("term_exact")

        for i, term_text in enumerate(term_inputs):
            if term_text.strip():
                terms.append(
                    {
                        "term": term_text.strip(),
                        "exact": exact_inputs[i] == "on"
                        if i < len(exact_inputs)
                        else True,
                    }
                )

        # Processar emails
        mail_to = [
            email.strip() for email in request.form.getlist("mail_to") if email.strip()
        ]

        # Montar dados da configuração
        config_data = {
            "label": data.get("label", "").strip(),
            "description": data.get("description", "").strip(),
            "attach_csv": data.get("attach_csv") == "on",
            "mail_to": mail_to,
            "mail_subject": data.get("mail_subject", "").strip(),
            "teams_webhook": None,  # Teams removido da interface
            "terms": terms,
            "active": data.get("active") == "on",
        }

        try:
            # Validar com Pydantic
            config_update = SearchConfigUpdate.model_validate(config_data)
            updated_config = service.update_config(
                config_id, config_update, user_id=current_user.id
            )

            if updated_config:
                flash("Configuração atualizada com sucesso!", "success")
                return redirect(url_for("web.index"))
            flash("Erro ao atualizar configuração", "error")

        except ValidationError as e:
            # Mapear erros do Pydantic para o template
            errors = {}
            for err in e.errors():
                loc = err["loc"]
                field = loc[0] if loc else "geral"
                msg = err["msg"]
                errors[str(field)] = msg

            return render_template(
                "edit.html", config=config, errors=errors, form_data=config_data
            )

        except Exception as e:  # noqa: BLE001  # noqa: BLE001  # noqa: BLE001
            flash(f"Erro ao atualizar configuração: {e!s}", "error")

    # Preparar dados do formulário
    form_data = {
        "label": config.label,
        "description": config.description,
        "attach_csv": config.attach_csv,
        "mail_to": config.mail_to,
        "mail_subject": config.mail_subject,
        "teams_webhook": "",  # Teams removido da interface
        "terms": [{"term": t.term, "exact": t.exact} for t in config.terms],
        "active": config.active,
    }

    return render_template("edit.html", config=config, errors={}, form_data=form_data)


@bp.route("/configs/<int:config_id>/delete", methods=["POST"])
@login_required
def delete_config(config_id: int) -> Any:
    """Deletar configuração (apenas do dono)."""
    service = get_service()
    deleted = service.delete_config(config_id, user_id=current_user.id)
    if deleted:
        flash("Configuração deletada com sucesso!", "success")
    else:
        flash("Configuração não encontrada", "error")
    return redirect(url_for("web.index"))


def _render_backtest(
    config: Any, result: dict[str, Any] | None = None, test_date: date | None = None
) -> Any:
    today = datetime.now(UTC).date()
    return render_template(
        "backtest.html",
        config=config,
        result=result,
        test_date=test_date,
        max_date=today.isoformat(),
    )


def _ensure_pages_exist(source: SearchSource, test_date: date) -> bool:
    if source.has_pages(test_date):
        return True
    try:
        response = consulta_por_data(test_date)
        arquivo = response.dados.arquivo_caderno_principal.arquivo
        paginas_iof = convert_pages(arquivo, test_date)
        paginas = [
            SearchPagina(
                titulo="",
                num_pagina=p.num_pagina,
                descricao="",
                conteudo=p.conteudo,
                data_publicacao=p.data_publicacao,
            )
            for p in paginas_iof
        ]
        source.import_pages(paginas)
    except Exception as e:  # noqa: BLE001
        error_msg = str(e).lower()
        if "not found" in error_msg or "404" in error_msg:
            flash(f"Diário não encontrado para {test_date}", "error")
        else:
            flash(f"Erro ao baixar diário: {e!s}", "error")
        return False
    else:
        flash(f"Diário de {test_date} baixado e importado com sucesso", "success")
        return True


def _get_valid_date(date_str: str | None) -> date | None:
    if not date_str:
        flash("Data é obrigatória", "error")
        return None
    try:
        test_date = date.fromisoformat(date_str)
    except ValueError:
        flash("Data inválida. Use o formato YYYY-MM-DD", "error")
        return None
    if test_date > datetime.now(UTC).date():
        flash("Não é possível testar datas futuras", "error")
        return None
    return test_date


def _send_backtest_email(config: Any, report: Any) -> None:
    provider_name = str(current_app.config.get("MAIL_PROVIDER", "smtp"))
    try:
        mailer = Mailer(current_app)
        config_error = mailer.validate_configuration()
        if config_error:
            flash(config_error, "warning")
            return

        subject = config.mail_subject or "Teste de Busca - Diário Oficial"
        email = notification_email(
            config.mail_to,
            report,
            subject=subject,
            attach_csv=config.attach_csv,
        )
        results = mailer.send(email)
        csv_info = " com CSV anexado" if config.attach_csv and report.count > 0 else ""
        message_id = results[0].message_id if results else None
        provider_info = f" via {provider_name.upper()}"
        message_id_info = f" (id {message_id})" if message_id else ""
        flash(
            f"Email de teste enviado com sucesso para {len(config.mail_to)} "
            f"destinatário(s)!{csv_info}{provider_info}{message_id_info}",
            "success",
        )
    except (ConnectionRefusedError, OSError) as e:
        mail_server = current_app.config.get("MAIL_SERVER", "")
        mail_port = current_app.config.get("MAIL_PORT", 0)
        error_code = getattr(e, "errno", None)
        if error_code == 61 or "Connection refused" in str(e) or "[Errno 61]" in str(e):
            tls_hint = (
                " Verifique também se MAIL_USE_TLS está configurado corretamente "
                "(para Gmail na porta 587, deve ser true)."
                if "gmail" in mail_server.lower()
                else ""
            )
            flash(
                f"Erro ao conectar ao servidor SMTP ({mail_server}:{mail_port}). "
                f"O servidor não está acessível ou não está rodando.{tls_hint} "
                "Verifique: 1) Se o servidor SMTP está acessível, "
                "2) Se as configurações MAIL_SMTP_HOST e MAIL_SMTP_PORT estão corretas "
                "no arquivo .env, 3) Se há firewall bloqueando a conexão.",
                "error",
            )
        else:
            flash(f"Erro de connection com o servidor SMTP: {e!s}", "error")
    except Exception as e:  # noqa: BLE001
        error_msg = str(e)
        if provider_name == "azure":
            error_msg_lower = error_msg.lower()
            if "sender" in error_msg_lower or "domain" in error_msg_lower:
                flash(
                    "Erro ao enviar via Azure Email. Verifique se "
                    "AZURE_EMAIL_SENDER_ADDRESS pertence ao domínio configurado no "
                    "Azure Communication Services.",
                    "error",
                )
            elif (
                "connection string" in error_msg_lower
                or "credential" in error_msg_lower
            ):
                flash(
                    "Erro de autenticação no Azure Email. Verifique "
                    "AZURE_COMMUNICATION_CONNECTION_STRING e AZURE_EMAIL_ENDPOINT.",
                    "error",
                )
            else:
                flash(
                    f"Erro ao enviar email via Azure Email: {error_msg}",
                    "error",
                )
        elif (
            "authentication" in error_msg.lower()
            or "login" in error_msg.lower()
            or "535" in error_msg
        ):
            flash(
                "Erro de autenticação no servidor SMTP. Verifique se MAIL_SMTP_USER "
                "e MAIL_SMTP_PASSWORD estão corretos no arquivo .env. Para Gmail, "
                'certifique-se de usar uma "Senha de App" e não sua senha normal.',
                "error",
            )
        elif "timeout" in error_msg.lower():
            flash(
                f"Timeout ao conectar ao servidor SMTP ({mail_server}:{mail_port}). "
                "Verifique se o servidor está acessível e sua conexão com a internet.",
                "error",
            )
        else:
            flash(
                f"Erro ao enviar email: {error_msg}. "
                "Verifique as configurações de email no arquivo .env.",
                "error",
            )


@bp.route("/configs/<int:config_id>/backtest", methods=["GET", "POST"])
@login_required
def backtest_config(config_id: int) -> Any:
    """Página de backtest (apenas do dono)."""
    service = get_service()
    config = service.get_config(config_id, user_id=current_user.id)
    if not config:
        flash("Configuração não encontrada", "error")
        return redirect(url_for("web.index"))

    app_env = os.getenv("APP_ENV", "development")
    if app_env != "development":
        flash("Backtest disponível apenas em ambiente de desenvolvimento", "error")
        return redirect(url_for("web.detail_config", config_id=config_id))

    if request.method != "POST":
        return _render_backtest(config)

    test_date = _get_valid_date(request.form.get("date"))
    if not test_date:
        return _render_backtest(config)

    diarios_dir = current_app.config.get("DIARIOS_DIR", "diarios")
    Path(diarios_dir).mkdir(parents=True, exist_ok=True)
    search_db = str(Path(diarios_dir) / "diarios.db")
    source = SearchSource(search_db)

    try:
        if not _ensure_pages_exist(source, test_date):
            return _render_backtest(config)

        search_terms = [Term(term=t.term, exact=t.exact) for t in config.terms]
        report = source.lookup(Trigger.BACKTEST, test_date, search_terms)

        result = {
            "publish_date": report.publish_date.isoformat(),
            "highlights": [
                {
                    "page": h.page,
                    "content": h.content,
                    "term": h.term,
                    "page_url": h.page_url,
                }
                for h in report.highlights
            ],
            "search_terms": [
                {"term": t.term, "exact": t.exact} for t in report.search_terms
            ],
            "trigger": report.trigger.value,
            "count": report.count,
        }

        if report.count > 0 and config.mail_to:
            _send_backtest_email(config, report)

        return _render_backtest(config, result=result, test_date=test_date)

    except Exception as e:
        current_app.logger.exception("Erro ao executar backtest")
        flash(f"Erro ao executar backtest: {e!s}", "error")
        return _render_backtest(config)
    finally:
        source.close()


# Registrar rotas de autenticação (login/logout)
from app.web import auth  # noqa: E402

auth.register(bp)
