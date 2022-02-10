from dataclasses import dataclass

from flask import Blueprint, render_template

from ..config import SonarrConfig
from ..models import Source
from ..sonarr import Series, Sonarr

bp = Blueprint("ui", __name__)


@dataclass
class SeriesSource:
    series: Series
    source: Source


def _sort_key(s: SeriesSource):
    return s.series.sort_title, s.source.season


@bp.route("/")
def ui():
    sonarr_config = SonarrConfig()
    sonnar = Sonarr(sonarr_config)

    series = sonnar.series()

    series_sources = sorted(
        [SeriesSource(series[s.tvdb_id], s) for s in Source.query],
        key=_sort_key,
    )

    return render_template("index.html", series_sources=series_sources)
