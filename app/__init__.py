"""
Application factory for the Pneumonia Detection System.

Usage:
    from app import create_app
    app = create_app('development')
"""
import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template

from app.config import config_map
from app.extensions import csrf, server_session
from app.models.db import init_app as init_db


def create_app(env: str = 'development') -> Flask:
    """
    Create and configure a Flask application instance.

    Args:
        env: One of 'development', 'testing', 'production'.

    Returns:
        Configured Flask app.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # ── Load configuration ─────────────────────────────────────
    cfg = config_map.get(env, config_map['default'])
    app.config.from_object(cfg)

    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config.get('SESSION_FILE_DIR', 'flask_session'), exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    # ── Logging ────────────────────────────────────────────────
    _configure_logging(app)

    # ── Extensions ─────────────────────────────────────────────
    csrf.init_app(app)
    server_session.init_app(app)

    # ── Database teardown ──────────────────────────────────────
    init_db(app)

    # ── Blueprints ─────────────────────────────────────────────
    from app.main import main_bp
    from app.auth import auth_bp
    from app.prediction import pred_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pred_bp)

    # ── Error handlers ─────────────────────────────────────────
    _register_error_handlers(app)

    # ── ML model warm-up (non-blocking) ───────────────────────
    _warm_up_model(app)

    app.logger.info('PneumoDetect started in [%s] mode.', env.upper())
    return app


# ── Private helpers ────────────────────────────────────────────────────────


def _configure_logging(app: Flask) -> None:
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # File handler (rotating, max 5 MB, keep 3 backups)
    log_file = app.config.get('LOG_FILE', 'logs/app.log')
    try:
        file_handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
    except Exception as exc:
        print(f'Warning: could not set up file logging: {exc}')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    app.logger.addHandler(console_handler)

    app.logger.setLevel(log_level)
    # Suppress werkzeug noise in production
    if not app.debug:
        logging.getLogger('werkzeug').setLevel(logging.ERROR)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html', title='Page Not Found'), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error('Server error: %s', e)
        return render_template('errors/500.html', title='Server Error'), 500

    @app.errorhandler(413)
    def file_too_large(e):
        from flask import flash, redirect, url_for
        flash('File is too large. Maximum upload size is 5 MB.', 'danger')
        return redirect(url_for('prediction.user_home'))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/404.html', title='Forbidden'), 403


def _warm_up_model(app: Flask) -> None:
    """Pre-load the active model into memory at startup."""
    with app.app_context():
        from app.prediction.predictor import warm_up
        warm_up(
            model_name=app.config.get('ACTIVE_MODEL', 'resnet50'),
            model_dir=app.config.get('MODEL_DIR', 'saved_models'),
        )
