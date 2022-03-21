from __future__ import annotations

import bisect
from dataclasses import dataclass
from functools import cached_property
from typing import List

from flask import Blueprint, redirect, render_template, url_for

from ...models import Source
from ...sonarr import Series, get_sonarr

bp = Blueprint("index", __name__)


@dataclass
class SeriesSource:
    series: Series
    source: Source

    def __lt__(self, other: SeriesSource):
        return (self.series.sort_title, self.source.season, self.source.id) < (
            other.series.sort_title,
            other.source.season,
            other.source.id,
        )

    @cached_property
    def completed(self):
        return self.series.completed(self.source.season)

    @property
    def season(self):
        return {-1: "All Seasons", 0: "Specials"}.get(
            self.source.season, self.source.season
        )


@bp.route("/")
def index():
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings.settings"))

    series_sources: List[SeriesSource] = []
    for source in Source.query:
        source: Source
        try:
            s = sonarr.get_series(source.tvdb_id)
        except KeyError:
            source.delete()
        else:
            bisect.insort(series_sources, SeriesSource(s, source))

    return render_template("index.html", series_sources=series_sources)
