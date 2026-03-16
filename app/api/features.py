"""API de features disponíveis."""

import os
from typing import Any

from flask import Blueprint, jsonify

bp = Blueprint("features", __name__, url_prefix="/api/features")


@bp.route("", methods=["GET"])
def get_features() -> tuple[Any, int]:
    """Retorna features habilitadas pela API."""
    # Por enquanto, backtest só em desenvolvimento
    app_env = os.getenv("APP_ENV", "development")
    backtest_enabled = app_env == "development"

    return jsonify({"backtest": backtest_enabled}), 200
