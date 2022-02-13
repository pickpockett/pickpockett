import logging
from datetime import datetime

from . import db
from .magnet import Magnet

logger = logging.getLogger(__name__)

ALL_SEASONS = -1
DEFAULT_QUALITY = "WEBRip-1080p"


class Source(db.Model):
    __tablename__ = "sources"

    id = db.Column(db.Integer, primary_key=True)
    tvdb_id = db.Column(db.Integer, nullable=False)
    season: db.Column = db.Column(
        db.Integer, nullable=False, server_default=str(ALL_SEASONS)
    )
    url = db.Column(db.Text, nullable=False)
    cookies = db.Column(db.Text, nullable=False, server_default="")
    hash = db.Column(db.String(40), nullable=False, server_default="")
    datetime = db.Column(db.DateTime)
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

    @property
    def updated(self):
        if self.datetime is None:
            return ""

        days = (datetime.utcnow().date() - self.datetime.date()).days

        if days == 0:
            return "Today"
        elif days == 1:
            return "Yesterday"
        elif days < 0:
            return "O_o"
        else:
            return f"{days} days ago"
