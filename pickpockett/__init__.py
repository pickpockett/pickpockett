import os
from multiprocessing import Process
from pathlib import Path

from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_migrate import Migrate, upgrade
from flask_sqlalchemy import SQLAlchemy

from . import filters
from .configuration import Config, ConfigManager

bootstrap = Bootstrap5()
config = ConfigManager()
db = SQLAlchemy()
migrate = Migrate()


class App(Flask):
    def __init__(self):
        from .blueprints import api, ui

        super().__init__(__name__)

        self.register_blueprint(api.bp)
        self.register_blueprint(ui.bp)

        self.jinja_env.trim_blocks = True
        self.jinja_env.lstrip_blocks = True
        filters.register(self)

        self.config["WTF_CSRF_ENABLED"] = False

        self.config["BOOTSTRAP_SERVE_LOCAL"] = True
        bootstrap.init_app(self)

        data_dir = Path(os.environ.get("DATA_DIR", os.getcwd()))
        config.path = data_dir / "config.json"

        db_uri = "sqlite:///" + str(data_dir / __name__) + ".db"
        self.config["SQLALCHEMY_DATABASE_URI"] = db_uri
        self.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        db.init_app(self)
        migrate.init_app(self, db)

        def db_upgrade():
            with self.app_context():
                upgrade()

        upgrade_process = Process(target=db_upgrade)
        upgrade_process.start()
        upgrade_process.join()
