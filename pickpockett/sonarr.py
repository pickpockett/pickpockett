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


def get_title(tvdb_id, sonarr):
    url = (
        f"http://{sonarr.host}:{sonarr.port}/api/series?"
        f"apikey={sonarr.apikey}"
    )
    r = requests.get(url)
    if not r.ok:
        return

    for show in r.json():
        if show["tvdbId"] == tvdb_id:
            return show["title"]
