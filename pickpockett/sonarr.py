import urllib.parse

import requests

from .db import Config


class Sonarr:
    _prefix = "sonarr_"

    @classmethod
    def load(cls, session):
        obj = Sonarr()
        for setting in session.query(Config).filter(
            Config.name.startswith(cls._prefix)
        ):
            name = setting.name.split(cls._prefix, 1)[1]
            setattr(obj, name, setting.value)
        return obj


def get_tvdb_id(title, sonarr):
    term = urllib.parse.quote(title)
    url = (
        f"http://{sonarr.host}:{sonarr.port}/api/series/lookup?"
        f"apikey={sonarr.apikey}&term={term}"
    )
    r = requests.get(url)
    if r.ok:
        result = r.json()
        return result[0]["tvdbId"]
