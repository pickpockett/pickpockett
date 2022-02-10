from dataclasses import dataclass

from flask import Blueprint, render_template

from pickpockett.config import SonarrConfig
from pickpockett.models import Source
from pickpockett.sonarr import Sonarr

bp = Blueprint("ui", __name__)


@dataclass
class SeriesSource:
    title: str
    source: Source

    @property
    def short_title(self):
        return self.title.lower().removeprefix("a").removeprefix("the").strip()


@bp.route("/")
def ui():
    sonarr_config = SonarrConfig()
    sonnar = Sonarr(sonarr_config)

    titles = sonnar.get_titles()

    series_sources = sorted(
        [SeriesSource(titles[s.tvdb_id], s) for s in Source.query],
        key=lambda s: (s.short_title, s.source.season),
    )

    return render_template("index.html", series_sources=series_sources)
