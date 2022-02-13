from dataclasses import dataclass

from flask import Blueprint, redirect, render_template, request, url_for

from .. import config, db
from ..forms import ConfigForm, SourceForm
from ..magnet import get_magnet
from ..models import DEFAULT_QUALITY, Source
from ..sonarr import Series, get_sonarr

bp = Blueprint("ui", __name__)


@dataclass
class SeriesSource:
    series: Series
    source: Source


def _sort_key(s: SeriesSource):
    return s.series.sort_title, s.source.season


@bp.route("/")
def index():
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings"))

    series = sonarr.series_dict()

    series_sources = sorted(
        [SeriesSource(series[s.tvdb_id], s) for s in Source.query],
        key=_sort_key,
    )

    return render_template("index.html", series_sources=series_sources)


@bp.route("/edit/<int:source_id>", methods=["GET", "POST"])
def edit(source_id):
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings"))

    source = Source.query.get(source_id)
    series = sonarr.get_series(source.tvdb_id)

    form = SourceForm(obj=source)
    form.season_choices(series.seasons)
    form.language_choices(sonarr.get_languages())
    form.quality_choices(sonarr.get_qualities(), source.quality)

    if request.method == "POST" and form.validate_on_submit():
        magnet, err = get_magnet(form.url.data, form.cookies.data)
        if err:
            form.url.errors = [err]
        else:
            source.url = form.url.data
            source.season = form.season.data
            source.cookies = magnet.cookies
            source.quality = form.quality.data
            source.language = form.language.data
            db.session.commit()
            return redirect(url_for("ui.index"))
    elif source.error:
        form.url.errors = [source.error]

    return render_template(
        "edit.html", form=form, series=series, source=source
    )


@bp.route("/edit/<int:source_id>/delete", methods=["POST"])
def delete(source_id):
    Source.query.filter_by(id=source_id).delete()
    db.session.commit()
    return redirect(url_for("ui.index"))


@bp.route("/add")
def add():
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings"))

    series = sonarr.series_sorted()

    return render_template("add.html", series=series)


@bp.route("/add/<int:tvdb_id>", methods=["GET", "POST"])
def add_source(tvdb_id):
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings"))

    series = sonarr.get_series(tvdb_id)

    form = SourceForm()
    form.season_choices(series.seasons)
    form.season.data = str(series.seasons[-1].season_number)
    form.language_choices(sonarr.get_languages())
    form.quality_choices(sonarr.get_qualities())
    form.quality.data = DEFAULT_QUALITY

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

    return render_template("add_source.html", form=form, series=series)


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    conf = config.load()
    form = ConfigForm(obj=conf)

    if request.method == "POST" and form.validate_on_submit():
        config.save(form.data)
        return redirect(url_for("ui.index"))

    return render_template("settings.html", form=form)
