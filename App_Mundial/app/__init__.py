import os

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        DATABASE="mundial.db",
        STORAGE_BACKEND=os.environ.get("STORAGE_BACKEND", "supabase"),
        SUPABASE_URL=os.environ.get("SUPABASE_URL"),
        SUPABASE_SERVICE_ROLE_KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    )
    if test_config:
        app.config.update(test_config)

    if app.config["STORAGE_BACKEND"] == "sqlite":
        from app import db

        db.init_app(app)

    from app.routes.public import public_bp

    app.register_blueprint(public_bp)
    return app
