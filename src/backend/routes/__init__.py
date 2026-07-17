from .auth import auth_bp
from .dashboard import dashboard_bp
from .media import media_bp
from .records import records_bp
from .stream import stream_bp


def register_routes(app):
    for blueprint in (auth_bp, dashboard_bp, records_bp, media_bp, stream_bp):
        app.register_blueprint(blueprint)
