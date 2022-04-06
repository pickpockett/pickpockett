from datetime import datetime

from flask import Flask
from humanize import naturaltime
from markupsafe import Markup


def naturalize(value):
    if value is None:
        return ""

    now = datetime.utcnow()
    msg = naturaltime(value, when=now)
    if (now - value).total_seconds() < 86400:
        msg = f"<b>{msg}</b>"

    return Markup(msg)


def register(app: Flask):
    app.add_template_filter(naturalize)
