import logging
import os

from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy

logging.basicConfig(level=logging.INFO)

db = SQLAlchemy()
bootstrap = Bootstrap5()


def init_app():
    from .blueprints import api, ui

    app = Flask(__name__)
    app.register_blueprint(api.bp)
    app.register_blueprint(ui.bp)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    app.config["BOOTSTRAP_SERVE_LOCAL"] = True
    bootstrap.init_app(app)

    db_dir = os.environ.get("db", os.getcwd())
    db_uri = "sqlite:///" + os.path.join(db_dir, __name__) + ".db"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    db.create_all(app=app)

    return app


app = init_app()
