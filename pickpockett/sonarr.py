from datetime import datetime
from typing import List
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, parse_obj_as, validator


class Series(BaseModel):
    id: int
    title: str
    tvdb_id: int

    class Config:
        fields = {"tvdb_id": "tvdbId"}


class Episode(BaseModel):
    season_number: int
    episode_number: int
    air_date_utc: datetime = None
    has_file: bool

    class Config:
        fields = {
            "season_number": "seasonNumber",
            "episode_number": "episodeNumber",
            "air_date_utc": "airDateUtc",
            "has_file": "hasFile",
        }

    @validator("air_date_utc")
    def convert_status(cls, air_date_utc: datetime):
        return air_date_utc.replace(tzinfo=None)


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

    def episode(self, series_id: int) -> List[Episode]:
        episode = self._get("episode", seriesId=series_id)
        episode_list = parse_obj_as(List[Episode], episode)
        return episode_list

    def series(self) -> List[Series]:
        series = self._get("series")
        series_list = parse_obj_as(List[Series], series)
        return series_list

    def get_series(self, tvdb_id: int):
        series = self.series()
        return next(s for s in series if s.tvdb_id == tvdb_id)

    def get_missing(self, tvdb_id, season, dt):
        series = self.get_series(tvdb_id)
        episode = self.episode(series.id)
        missing = [
            ep
            for ep in episode
            if ep.season_number == season
            and ep.air_date_utc is not None
            and ep.air_date_utc < dt
            and ep.has_file is False
        ]
        return series.title, missing

    def get_titles(self):
        series = self.series()
        titles = {s.tvdb_id: s.title for s in series}
        return titles
