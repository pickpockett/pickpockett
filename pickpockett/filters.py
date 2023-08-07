from datetime import datetime

from flask import Flask
from humanize import naturaltime
from markupsafe import Markup

_pseudo_braille_table = str.maketrans("01234567", "⠂⠆⠖⠶⠷⡷⡿⣿")


def braille(value: int):
    a, b = divmod(value, 8)
    v = "7" * a + str(b)

    return v.translate(_pseudo_braille_table)


def naturalize(value):
    if value is None:
        return ""

    now = datetime.utcnow()
    msg = naturaltime(value, when=now)
    if (now - value).total_seconds() < 172800:
        msg = f"<b>{msg}</b>"

    return Markup(msg)


def register(app: Flask):
    app.add_template_filter(braille)
    app.add_template_filter(naturalize)
