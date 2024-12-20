from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    update,
)

from . import db
from .magnet import Magnet

logger = logging.getLogger(__name__)

ALL_SEASONS = -1
DEFAULT_QUALITY = "WEBRip-1080p"


class Source(db.Model):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    tvdb_id = Column(Integer, nullable=False)
    season: Column = Column(
        Integer, nullable=False, server_default=str(ALL_SEASONS)
    )
    url = Column(Text, nullable=False)
    schedule_correction = Column(Integer, nullable=False, server_default="0")
    cookies = Column(JSON, nullable=False, server_default="{}")
    user_agent = Column(Text, nullable=False, server_default="")
    hash = Column(String(40), nullable=False, server_default="")
    datetime = Column(DateTime)
    quality = Column(Text, nullable=False, default=DEFAULT_QUALITY)
    language = Column(Text, nullable=False, server_default="")
    error = Column(Text, nullable=False, server_default="")
    version = Column(Integer, nullable=False, server_default="0")
    announcement = Column(Boolean, nullable=False, server_default="0")
    report_existing = Column(Boolean, nullable=False, server_default="0")

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

    def update(self, cookies=None, **kwargs):
        if cookies is not None:
            self.update_cookies(cookies)
        for key, value in kwargs.items():
            setattr(self, key, value)
        db.session.commit()

    @property
    def extra(self):
        return ", ".join(e for e in (self.language, self.quality) if e)

    def update_cookies(self, new):
        if self.cookies and new:
            db.session.execute(
                update(self.__class__)
                .where(self.__class__.cookies == self.cookies)
                .values(cookies=new, error="")
            )
        else:
            self.cookies = new
            self.error = ""

    def update_magnet(self, magnet: Magnet):
        cookies = {
            key: value
            for key, value in magnet.cookies.items()
            if key in self.cookies or not self.cookies
        }
        self.update_cookies(cookies)
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
            self.version += 1
            self.announcement = False
        db.session.commit()

    def update_error(self, err):
        self.error = err or ""
        db.session.commit()

    def refresh(self):
        db.session.refresh(self)
