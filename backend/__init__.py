from flask import Flask

from backend.config import PROJECT_ROOT, SECRET_KEY
from backend.routes import auth_bp, dashboard_bp, media_bp, records_bp, stream_bp
from backend.services.fine_store import FineCaseStore


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    store = FineCaseStore(PROJECT_ROOT)
    app.extensions["fine_store"] = store

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(stream_bp)

    return app
