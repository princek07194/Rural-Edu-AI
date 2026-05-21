"""Flask application factory."""
import logging
import os
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import config_by_name
from app.extensions import db, jwt, limiter


def create_app(config_name=None):
    """Create and configure Flask application."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # SQLite: avoid "database is locked" on Windows during register/login
    if "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"check_same_thread": False, "timeout": 30},
        }

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.videos import videos_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.download import download_bp
    from app.routes.translate import translate_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admin import admin_bp
    from app.routes.bookmarks import bookmarks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(translate_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(bookmarks_bp)

    # Health check
    @app.route("/api/health")
    def health():
        from app.services.ai_service import get_ai_mode, is_cloud_ai_configured
        return jsonify({
            "status": "ok",
            "service": "Rural Education API",
            "ai_mode": get_ai_mode(),
            "ai_configured": is_cloud_ai_configured(),
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(429)
    def rate_limit(e):
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

    @app.errorhandler(500)
    def server_error(e):
        msg = "Internal server error"
        if app.debug and e and getattr(e, "description", None):
            msg = str(e.description)
        return jsonify({"error": msg}), 500

    # Create tables
    with app.app_context():
        try:
            db.create_all()
            uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            if "sqlite" in uri:
                logging.getLogger(__name__).info("Using SQLite database (local dev)")
            else:
                logging.getLogger(__name__).info("Using MySQL database")
        except Exception as e:
            logging.getLogger(__name__).error("Failed to create database tables: %s", e)

    return app
