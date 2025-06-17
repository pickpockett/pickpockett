import logging
from datetime import datetime

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

        for source in Source.query:
            update_magnet(source, g.webhook)


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
