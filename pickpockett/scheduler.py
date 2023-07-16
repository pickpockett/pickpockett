import logging
from datetime import datetime, timedelta

from flask import Flask, g
from flask_apscheduler import APScheduler

from . import Config, config
from .magnet import get_magnet
from .models import Source
from .sonarr import Sonarr

logger = logging.getLogger(__name__)

scheduler = APScheduler()


def check():
    with scheduler.app.app_context():
        g.config = config.load()

        if not g.config.sonarr:
            return

        sonarr = Sonarr(g.config.sonarr)

        for source in Source.query:
            if not source.error and source.datetime:
                series = sonarr.get_series(source.tvdb_id)
                if series is None:
                    continue

                schedule_correction = timedelta(
                    days=source.schedule_correction
                )
                now = datetime.utcnow() + schedule_correction

                episodes = series.get_episodes(source.season, now)
                last_aired = max(ep.air_date_utc for ep in episodes)

                if last_aired < source.datetime:
                    continue

            magnet, err = get_magnet(
                source.url, source.cookies, source.user_agent
            )
            source.update_error(err)

            if magnet and magnet.url is None:
                logger.error(
                    "[tvdbid:%i]: no magnet link found: %r",
                    source.tvdb_id,
                    source.url,
                )
                continue
            if err:
                logger.error("[tvdbid:%i]: error: %s", source.tvdb_id, err)
                continue

            source.update_magnet(magnet)


def reschedule(conf: Config):
    scheduler.remove_all_jobs()
    scheduler.add_job(
        check.__name__,
        check,
        trigger="interval",
        minutes=conf.general.check_interval,
    )


def init_app(app: Flask):
    scheduler.init_app(app)
    scheduler.start()
