import logging
from datetime import datetime

from . import db
from .magnet import Magnet

logger = logging.getLogger(__name__)

DEFAULT_QUALITY = "WEBRip-1080p"


class Config(db.Model):
    __tablename__ = "config"

    name = db.Column(db.Text, primary_key=True)
    value = db.Column(db.Text)


class Source(db.Model):
    __tablename__ = "sources"

    id = db.Column(db.Integer, primary_key=True)
    tvdb_id = db.Column(db.Integer, nullable=False)
    season = db.Column(db.Integer, nullable=False, server_default="-1")
    url = db.Column(db.Text, nullable=False, server_default="")
    cookies = db.Column(db.Text, nullable=False, server_default="")
    hash = db.Column(db.String(40), nullable=False, server_default="")
    datetime = db.Column(
        db.DateTime, nullable=False, server_default="0001-01-01 00:00:00"
    )
    quality = db.Column(db.Text, nullable=False, default=DEFAULT_QUALITY)
    language = db.Column(db.Text, nullable=False, server_default="")
    error = db.Column(db.Text, nullable=False, server_default="")

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        db.session.add(obj)
        db.session.commit()

    @property
    def extra(self):
        return ", ".join(e for e in (self.language, self.quality) if e)

    def update_magnet(self, magnet: Magnet):
        if self.hash != magnet.hash:
            logger.info(
                "[tbdbid:%i]: hash update: %r => %r",
                self.tvdb_id,
                self.hash,
                magnet.hash,
            )
            self.hash = magnet.hash
            self.datetime = datetime.utcnow()
            db.session.commit()

    def update_error(self, err):
        self.error = err or ""
        db.session.commit()