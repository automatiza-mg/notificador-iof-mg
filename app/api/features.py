"""API de features disponíveis."""
from flask import Blueprint, jsonify
from app import create_app

bp = Blueprint('features', __name__, url_prefix='/api/features')


@bp.route('', methods=['GET'])
def get_features():
    """Retorna features habilitadas pela API."""
    # Por enquanto, backtest só em desenvolvimento
    import os
    app_env = os.getenv('APP_ENV', 'development')
    backtest_enabled = app_env == 'development'
    
    return jsonify({
        'backtest': backtest_enabled
    }), 200

