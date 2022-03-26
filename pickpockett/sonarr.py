from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from itertools import chain
from typing import Dict, List, Literal, Optional
from urllib.parse import urljoin

import requests
from cachetools import TTLCache
from pydantic import BaseModel, parse_obj_as, validator

from .models import ALL_SEASONS

logger = logging.getLogger(__name__)


class Image(BaseModel):
    cover_type: Literal["banner", "fanart", "poster"]
    url: str

    class Config:
        fields = {"cover_type": "coverType"}


class Season(BaseModel):
    season_number: int

    class Config:
        fields = {"season_number": "seasonNumber"}


class Series(BaseModel):
    id: int
    title: str
    sort_title: str
    tvdb_id: int
    images: List[Image]
    seasons: List[Season]
    season_count: int
    status: str
    sonarr: Sonarr

    class Config:
        arbitrary_types_allowed = True
        fields = {
            "season_count": "seasonCount",
            "sort_title": "sortTitle",
            "tvdb_id": "tvdbId",
        }

    def __lt__(self, other: Series):
        return self.sort_title < other.sort_title

    def image(self, cover_type: Literal["banner", "fanart", "poster"]):
        return next(i for i in self.images if i.cover_type == cover_type)

    @property
    def poster(self):
        return urljoin(self.sonarr.url, self.image("poster").url)

    def completed(self, season):
        episode = self.sonarr.episode(self.id)
        exist = [
            ep.has_file
            for ep in episode
            if ep.season_number == season
            or season == ALL_SEASONS
            and self.status == "ended"
            and ep.season_number > 0
        ]
        return exist and all(exist)

    def get_episodes(self, season, dt, missing=False) -> List[Episode]:
        episode = self.sonarr.episode(self.id)
        season_episode_list = [
            ep
            for ep in episode
            if ep.monitored
            and (not missing or not ep.has_file)
            and (season == ALL_SEASONS or ep.season_number == season)
            and ep.air_date_utc is not None
            and ep.air_date_utc < dt
        ]
        return season_episode_list


class SeriesLookup(BaseModel):
    profile_id: int
    season_count: int
    tvdb_id: int

    class Config:
        fields = {
            "profile_id": "profileId",
            "season_count": "seasonCount",
            "tvdb_id": "tvdbId",
        }


class Episode(BaseModel):
    season_number: int
    episode_number: int
    air_date_utc: Optional[datetime] = None
    has_file: bool
    monitored: bool

    class Config:
        fields = {
            "season_number": "seasonNumber",
            "episode_number": "episodeNumber",
            "air_date_utc": "airDateUtc",
            "has_file": "hasFile",
        }

    @validator("air_date_utc")
    def remove_tz(cls, air_date_utc: datetime):
        return air_date_utc.replace(tzinfo=None)


class Language(BaseModel):
    name: str


class LanguageItem(BaseModel):
    language: Language


class LanguageProfile(BaseModel):
    languages: List[LanguageItem]


class Quality(BaseModel):
    name: str


class QualityItem(BaseModel):
    quality: Quality


class QualityGroup(BaseModel):
    items: List[QualityItem]
    quality: Optional[Quality] = None


class QualityProfile(BaseModel):
    items: List[QualityGroup]


class ParsedEpisodeInfo(BaseModel):
    season_number: int
    language: Language
    quality: QualityItem

    class Config:
        fields = {"season_number": "seasonNumber"}


class SonarrCache(TTLCache):
    def __init__(self):
        super().__init__(3, ttl=timedelta(days=1).total_seconds())

    def get_cached(self, key, getter):
        try:
            return self[key]
        except KeyError:
            pass

        cached = self[key] = getter()
        return cached


class Sonarr:
    cache = SonarrCache()

    def __init__(self, sonarr_config):
        self.url = sonarr_config.url
        self.apikey = sonarr_config.apikey

    def _url(self, endpoint):
        return urljoin(self.url, f"api/{endpoint}")

    def _get(self, endpoint, **kwargs):
        url = self._url(endpoint)
        headers = {"User-Agent": "PickPockett"}
        params = {"apikey": self.apikey, **kwargs}
        r = requests.get(url, headers=headers, params=params)
        if r.ok:
            return r.json()
        return []

    def episode(self, series_id: int) -> List[Episode]:
        episode = self._get("episode", seriesId=series_id)
        episode_list = parse_obj_as(List[Episode], episode)
        return episode_list

    def _series(self) -> Dict[int, Series]:
        series = {
            (s := Series.parse_obj(dict(obj, sonarr=self))).tvdb_id: s
            for obj in self._get("series")
        }
        return series

    def series(self) -> List[Series]:
        series = self.cache["series"] = self._series()
        return sorted(series.values())

    def get_series(self, tvdb_id: int) -> Series:
        try:
            return self.cache.get_cached("series", self._series)[tvdb_id]
        except KeyError:
            pass
        series = self.cache["series"] = self._series()
        return series[tvdb_id]

    def _languages(self):
        language_profile = LanguageProfile.parse_obj(
            self._get("v3/languageprofile/schema")
        )
        return list(
            sorted(
                language_item.language.name
                for language_item in language_profile.languages
                if language_item.language.name != "Unknown"
            )
        )

    def get_languages(self):
        return self.cache.get_cached("language", self._languages)

    def _qualities(self):
        quality_profile = QualityProfile.parse_obj(
            self._get("v3/qualityprofile/schema")
        )
        qualities = [
            quality
            for quality in chain(
                *(
                    (quality.quality.name for quality in quality_group.items)
                    if quality_group.items
                    else [quality_group.quality.name]
                    for quality_group in quality_profile.items
                )
            )
            if quality != "Unknown"
        ]
        return qualities

    def get_qualities(self):
        return self.cache.get_cached("quality", self._qualities)

    def series_lookup(self, term):
        lookup = self._get("series/lookup", term=term)
        lookup_list = [
            series
            for series in parse_obj_as(List[SeriesLookup], lookup)
            if series.profile_id > 0
        ]
        return lookup_list

    def parse(self, title, *, strip=False):
        if strip:
            title = re.sub(r"[^\s\w]+", "", title, flags=re.ASCII)

        parsed = self._get("parse", title=title)
        if parsed_info := parsed.get("parsedEpisodeInfo"):
            return ParsedEpisodeInfo.parse_obj(parsed_info)


Series.update_forward_refs()
