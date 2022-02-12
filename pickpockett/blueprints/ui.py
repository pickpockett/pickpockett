from dataclasses import dataclass

from flask import Blueprint, render_template

from ..config import SonarrConfig
from ..forms import SourceForm
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
def index():
    sonarr_config = SonarrConfig()
    sonarr = Sonarr(sonarr_config)
    series = sonarr.series()

    series_sources = sorted(
        [SeriesSource(series[s.tvdb_id], s) for s in Source.query],
        key=_sort_key,
    )

    return render_template("index.html", series_sources=series_sources)


@bp.route("/edit/<int:source_id>")
def edit(source_id):
    source = Source.query.get(source_id)

    sonarr_config = SonarrConfig()
    sonarr = Sonarr(sonarr_config)
    series = sonarr.get_series(source.tvdb_id)

    form = SourceForm(obj=source)
    form.season_choices(series.seasons)
    form.language_choices(sonarr.get_languages())
    form.quality_choices(source.quality, sonarr.get_qualities())

    return render_template(
        "edit.html", form=form, series=series, source=source
    )
