from . import db


class Config(db.Model):
    __tablename__ = "config"

    name = db.Column(db.Text, primary_key=True)
    value = db.Column(db.Text)


class Source(db.Model):
    __tablename__ = "sources"

    id = db.Column(db.Integer, primary_key=True)
    tvdb_id = db.Column(db.Integer, nullable=False)
    season = db.Column(db.Integer, nullable=False, server_default="1")
    link = db.Column(db.Text, nullable=False, server_default="")
    cookies = db.Column(db.Text, nullable=False, server_default="")
    hash = db.Column(db.String(40), nullable=False, server_default="")
    datetime = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default="0001-01-01 0:00:00.000",
    )
