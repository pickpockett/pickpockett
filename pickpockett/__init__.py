import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db_dir = os.environ.get("db", os.getcwd())
db_uri = "sqlite:///" + os.path.join(db_dir, __name__) + ".db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
