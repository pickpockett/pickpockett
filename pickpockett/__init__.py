import logging
import os
from pathlib import Path

from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy

from .configuration import Config, ConfigManager

logging.basicConfig(level=logging.INFO)

db = SQLAlchemy()
bootstrap = Bootstrap5()
config = ConfigManager()


def init_app():
    from .blueprints import api, ui

    app = Flask(__name__)
    app.register_blueprint(api.bp)
    app.register_blueprint(ui.bp)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    app.config["WTF_CSRF_ENABLED"] = False

    app.config["BOOTSTRAP_SERVE_LOCAL"] = True
    bootstrap.init_app(app)

    data_dir = Path(os.environ.get("data", os.getcwd()))
    config.path = data_dir / "config.json"

    db_uri = "sqlite:///" + str(data_dir / __name__) + ".db"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    db.create_all(app=app)

    return app


app = init_app()
