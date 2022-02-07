from urllib.parse import urljoin

import requests


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

    def series(self):
        return self._get("series")

    def get_series(self, tvdb_id):
        series = self.series()
        for item in series:
            if item["tvdbId"] == tvdb_id:
                return item

    def get_title(self, tvdb_id):
        if series := self.get_series(tvdb_id):
            return series["title"]
