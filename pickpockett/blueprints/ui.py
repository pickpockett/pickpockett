from __future__ import annotations

import bisect
from dataclasses import dataclass
from functools import cached_property
from typing import List

from flask import Blueprint, redirect, render_template, request, url_for

from .. import config
from ..forms import ConfigForm, SourceForm
from ..magnet import get_magnet
from ..models import Source
from ..sonarr import Series, get_sonarr

bp = Blueprint("ui", __name__)


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
        return redirect(url_for("ui.settings"))

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


@bp.route("/edit/<int:source_id>", methods=["GET", "POST"])
def edit(source_id):
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings"))

    source = Source.get(source_id)
    series = sonarr.get_series(source.tvdb_id)

    form = SourceForm(obj=source)
    form.season_choices(series.seasons)
    form.language_choices(sonarr.get_languages())
    form.quality_choices(sonarr.get_qualities())

    if request.method == "POST" and form.validate_on_submit():
        magnet, err = get_magnet(form.url.data, form.cookies.data)
        if err:
            form.url.errors = [err]
        else:
            source.update(
                url=form.url.data,
                season=form.season.data,
                cookies=magnet.cookies,
                quality=form.quality.data,
                language=form.language.data,
                error="",
            )
            return redirect(url_for("ui.index"))
    elif source.error:
        form.url.errors = [source.error]

    return render_template(
        "edit.html", form=form, series=series, source=source
    )


@bp.route("/edit/<int:source_id>/delete", methods=["POST"])
def delete(source_id):
    Source.get(source_id).delete()
    return redirect(url_for("ui.index"))


@bp.route("/add")
def add():
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings"))

    series = sonarr.series()
    return render_template("add.html", series=series)


@bp.route("/add/<int:tvdb_id>", methods=["GET", "POST"])
def add_source(tvdb_id):
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings"))

    series = sonarr.get_series(tvdb_id)

    form = SourceForm()
    form.season_choices(series.seasons)
    form.language_choices(sonarr.get_languages())
    form.quality_choices(sonarr.get_qualities())

    if request.method == "POST" and form.validate_on_submit():
        magnet, err = get_magnet(form.url.data, form.cookies.data)
        if err:
            form.url.errors = [err]
        else:
            Source.create(
                tvdb_id=tvdb_id,
                url=form.url.data,
                season=form.season.data,
                cookies=magnet.cookies,
                quality=form.quality.data,
                language=form.language.data,
            )
            return redirect(url_for("ui.index"))
    else:
        form.season.data = series.seasons[-1].season_number

    return render_template("add_source.html", form=form, series=series)


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    conf = config.load()
    form = ConfigForm(obj=conf)

    if request.method == "POST" and form.validate_on_submit():
        config.save(form.data)
        return redirect(url_for("ui.index"))

    return render_template("settings.html", form=form)
