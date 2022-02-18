from __future__ import annotations

import logging
import os
from datetime import datetime

from humanize import naturaltime
from pytz import timezone

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

        tz, utc = timezone(os.environ.get("TZ") or "UTC"), timezone("UTC")
        dt = self.datetime.replace(tzinfo=utc).astimezone(tz)
        now = datetime.now(utc)
        return naturaltime(dt, when=now)
