from __future__ import annotations

import logging
from datetime import datetime

from humanize import naturaltime

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
    user_agent = db.Column(db.Text, nullable=False, server_default="")
    hash = db.Column(db.String(40), nullable=False, server_default="")
    datetime = db.Column(db.DateTime)
    quality = db.Column(db.Text, nullable=False, default=DEFAULT_QUALITY)
    language = db.Column(db.Text, nullable=False, server_default="")
    error = db.Column(db.Text, nullable=False, server_default="")

    @classmethod
    def get(cls, ident) -> Source:
        return cls.query.get(ident)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        db.session.add(obj)
        db.session.commit()
        return obj

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        db.session.commit()

    @property
    def extra(self):
        return ", ".join(e for e in (self.language, self.quality) if e)

    def update_magnet(self, magnet: Magnet):
        if magnet.cookies:
            self.cookies = magnet.cookies
        if magnet.user_agent:
            self.user_agent = magnet.user_agent
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

        return naturaltime(self.datetime, when=datetime.utcnow())
