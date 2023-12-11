import logging
from datetime import datetime, timedelta

from flask import Flask, g
from flask_apscheduler import APScheduler

from . import Config
from .blueprints import before_request
from .magnet import update_magnet
from .models import Source

logger = logging.getLogger(__name__)

scheduler = APScheduler()


def check():
    with scheduler.app.app_context():
        before_request()

        if not g.sonarr:
            return

        for source in Source.query:
            if not source.error and source.datetime and not source.cookies:
                series = g.sonarr.get_series(source.tvdb_id)
                if series is None:
                    continue

                schedule_correction = timedelta(
                    days=source.schedule_correction
                )
                now = datetime.utcnow() + schedule_correction

                episodes = series.get_episodes(source.season, now)
                last_aired = max(
                    ep.air_date_utc for ep in episodes if ep.air_date_utc
                )

                if last_aired < source.datetime:
                    continue

            update_magnet(source)


def reschedule(conf: Config):
    scheduler.remove_all_jobs()
    scheduler.add_job(
        check.__name__,
        check,
        trigger="interval",
        minutes=conf.general.check_interval,
    ).modify(next_run_time=datetime.now())


def init_app(app: Flask):
    scheduler.init_app(app)
    scheduler.start()
