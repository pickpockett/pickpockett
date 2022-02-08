from datetime import datetime
from typing import List
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, Field, parse_obj_as, validator


class Series(BaseModel):
    id: int
    title: str
    tvdb_id: int = Field(..., alias="tvdbId")


class Episode(BaseModel):
    season_number: int = Field(..., alias="seasonNumber")
    episode_number: int = Field(..., alias="episodeNumber")
    air_date_utc: datetime = Field(None, alias="airDateUtc")
    has_file: bool = Field(..., alias="hasFile")

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

    def episode(self, series_id):
        return self._get("episode", seriesId=series_id)

    def get_series(self, tvdb_id):
        series = self._get("series")
        series_list = parse_obj_as(List[Series], series)
        for item in series_list:
            if item.tvdb_id == tvdb_id:
                return item

    def get_missing(self, tvdb_id, season, dt):
        series = self.get_series(tvdb_id)
        episode = self.episode(series.id)
        episode_list = parse_obj_as(List[Episode], episode)
        missing = [
            ep
            for ep in episode_list
            if ep.season_number == season
            and ep.air_date_utc is not None
            and dt > ep.air_date_utc
            and ep.has_file is False
        ]
        return series.title, missing
