from . import db


class Config(db.Model):
    __tablename__ = "config"

    name = db.Column(db.Text, primary_key=True)
    value = db.Column(db.Text)


class Source(db.Model):
    __tablename__ = "sources"

    tvdb_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    season = db.Column(
        db.Integer, primary_key=True, autoincrement=False, nullable=True
    )
    link = db.Column(db.Text, nullable=False, server_default="")
    cookies = db.Column(db.Text, nullable=False, server_default="")
    hash = db.Column(db.String(40), nullable=False, server_default="")
    timestamp = db.Column(db.Integer, nullable=False, server_default="0")
