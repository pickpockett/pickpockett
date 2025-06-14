from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from itertools import chain
from typing import Callable, Dict, List, Literal, Optional
from urllib.parse import urljoin

import requests
from cachetools import TTLCache
from pydantic import (
    AliasChoices,
    AliasPath,
    BaseModel,
    Field,
    TypeAdapter,
    field_validator,
)

from .models import ALL_SEASONS

logger = logging.getLogger(__name__)


class Image(BaseModel):
    cover_type: Literal[
        "unknown",
        "poster",
        "banner",
        "fanart",
        "screenshot",
        "headshot",
        "clearlogo",
    ] = Field(alias="coverType")
    url: str = ""


class Season(BaseModel):
    season_number: int = Field(alias="seasonNumber")


season_count_alias = AliasPath("statistics", "seasonCount")


class Series(BaseModel):
    id: int
    title: str
    title_slug: str = Field(alias="titleSlug")
    sort_title: str = Field(alias="sortTitle")
    tvdb_id: int = Field(alias="tvdbId")
    images: List[Image]
    seasons: List[Season]
    season_count: int = Field(validation_alias=season_count_alias, default=0)
    status: str
    sonarr: Sonarr

    class Config:
        arbitrary_types_allowed = True

    def __lt__(self, other: Series):
        return self.sort_title < other.sort_title

    def image(self, cover_type: Literal["banner", "fanart", "poster"]):
        return next(
            (i for i in self.images if i.cover_type == cover_type),
            self.images[0],
        )

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

    def get_episodes(self, season, dt) -> List[Episode]:
        episode = self.sonarr.episode(self.id)
        season_episode_list = [
            ep
            for ep in episode
            if ep.monitored
            and season in (ALL_SEASONS, ep.season_number)
            and (ep.air_date_utc or datetime.max) < dt
        ]
        return season_episode_list

    def n_files(self, season: int) -> int:
        episode = self.sonarr.episode(self.id)
        return len(
            [
                ep
                for ep in episode
                if season in (ALL_SEASONS, ep.season_number) and ep.has_file
            ]
        )

    @property
    def url(self):
        return urljoin(self.sonarr.url, f"series/{self.title_slug}")


class SeriesLookup(BaseModel):
    quality_profile_id: int = Field(alias="qualityProfileId")
    season_count: int = Field(validation_alias=season_count_alias)
    tvdb_id: int = Field(alias="tvdbId")


class Episode(BaseModel):
    season_number: int = Field(alias="seasonNumber")
    episode_number: int = Field(alias="episodeNumber")
    air_date_utc: Optional[datetime] = Field(None, alias="airDateUtc")
    has_file: bool = Field(alias="hasFile")
    monitored: bool

    @field_validator("air_date_utc")
    @classmethod
    def remove_tz(cls, air_date_utc: datetime):
        return air_date_utc.replace(tzinfo=None)


class Language(BaseModel):
    id: int = Field(validation_alias=AliasChoices("id", "value"))
    name: str


class LanguageProfile(BaseModel):
    languages: List[Language] = Field(alias="selectOptions")


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
    season_number: int = Field(alias="seasonNumber")
    languages: List[Language]
    quality: QualityItem


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
        self.url = str(sonarr_config.url)
        self.apikey = sonarr_config.apikey

    def _url(self, endpoint):
        return urljoin(self.url, f"api/v3/{endpoint}")

    def _get(self, endpoint, default_factory: Callable = list, **kwargs):
        url = self._url(endpoint)
        headers = {"User-Agent": "PickPockett"}
        params = {"apikey": self.apikey, **kwargs}
        r = requests.get(url, headers=headers, params=params)
        if r.ok:
            return r.json()
        return default_factory()

    @property
    def icon(self):
        return urljoin(self.url, "Content/Images/logo.svg")

    def episode(self, series_id: int) -> List[Episode]:
        episode = self._get("episode", seriesId=series_id)
        episode_list = TypeAdapter(List[Episode]).validate_python(episode)
        return episode_list

    def _series(self) -> Dict[int, Series]:
        series = {
            (s := Series.model_validate(dict(obj, sonarr=self))).tvdb_id: s
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
        schema = self._get("customformat/schema")
        language_profile = LanguageProfile.model_validate(
            next(
                impl["fields"][0]
                for impl in schema
                if impl["implementationName"] == "Language"
            )
        )
        return list(
            sorted(
                language.name
                for language in language_profile.languages
                if language.id > 1
            )
        )

    def get_languages(self):
        return self.cache.get_cached("language", self._languages)

    def _qualities(self):
        quality_profile = QualityProfile.model_validate(
            self._get("qualityprofile/schema")
        )
        qualities = [
            quality
            for quality in chain(
                *(
                    (
                        (
                            quality.quality.name
                            for quality in quality_group.items
                        )
                        if quality_group.items
                        else [quality_group.quality.name]
                    )
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
            for series in TypeAdapter(List[SeriesLookup]).validate_python(
                lookup
            )
            if series.quality_profile_id > 0
        ]
        return lookup_list

    def parse(self, title, *, strip=False):
        if strip:
            title = re.sub(r"[^\s\w]+", "", title, flags=re.ASCII)

        parsed = self._get("parse", title=title)
        if parsed_info := parsed.get("parsedEpisodeInfo"):
            return ParsedEpisodeInfo.model_validate(parsed_info)

    def _downloaded(self, download_id: str) -> bool:
        history = self._get(
            "history",
            default_factory=dict,
            downloadId=download_id,
        )
        return history.get("totalRecords", 0) > 0

    def already_downloaded(self, source_hash: str):
        download_id = source_hash.upper()
        return self.cache.get_cached(
            download_id,
            lambda: self._downloaded(download_id),
        )


Series.model_rebuild()
