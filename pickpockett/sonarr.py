from datetime import datetime
from urllib.parse import urljoin

import requests


def _json_datetime(s):
    if s:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    return datetime(9999, 12, 31, 23, 59)


class Sonarr:
    def __init__(self, config):
        self.url = config.url
        self.apikey = config.apikey

    def _url(self, endpoint):
        return urljoin(self.url, f"api/{endpoint}")

    def _get(self, endpoint, **kwargs):
        url = self._url(endpoint)
        params = {"apikey": self.apikey, **kwargs}
        r = requests.get(url, params=params)
        if r.ok:
            return r.json()
        return []

    def episode(self, series_id):
        return self._get("episode", seriesId=series_id)

    def get_series(self, tvdb_id):
        series = self._get("series")
        for item in series:
            if item["tvdbId"] == tvdb_id:
                return item

    def get_missing(self, tvdb_id, season, dt):
        series = self.get_series(tvdb_id)
        episode = self.episode(series["id"])
        missing = [
            ep
            for ep in episode
            if ep["seasonNumber"] == season
            and dt > _json_datetime(ep.get("airDateUtc"))
            and ep["hasFile"] is False
        ]
        return series["title"], missing
