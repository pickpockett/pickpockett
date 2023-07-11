import logging
from concurrent import futures as concurrent
from datetime import datetime, timedelta

from flask import Flask, g
from flask.ctx import AppContext
from flask_apscheduler import APScheduler

from . import Config, config
from .magnet import update_magnet
from .models import Source
from .sonarr import Sonarr

logger = logging.getLogger(__name__)

scheduler = APScheduler()


def _update_source(context: AppContext, sonarr: Sonarr, source: Source):
    with context:
        if not source.error and source.datetime:
            series = sonarr.get_series(source.tvdb_id)
            if series is None:
                return

            schedule_correction = timedelta(days=source.schedule_correction)
            now = datetime.utcnow() + schedule_correction

            episodes = series.get_episodes(source.season, now)
            last_aired = max(ep.air_date_utc for ep in episodes)

            if last_aired < source.datetime:
                return

        update_magnet(source)


def check():
    with scheduler.app.app_context() as context:
        g.config = config.load()

        if not g.config.sonarr:
            return

        sonarr = Sonarr(g.config.sonarr)

        with concurrent.ThreadPoolExecutor() as executor:
            for source in Source.query:
                executor.submit(_update_source, context, sonarr, source)


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
