from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for

from ...forms.source import SourceForm
from ...magnet import get_magnet
from ...models import Source
from ...sonarr import get_sonarr

bp = Blueprint("edit", __name__, url_prefix="/edit")


@bp.route("/<int:source_id>", methods=["GET", "POST"])
def edit(source_id):
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings.settings"))

    source = Source.get(source_id)
    series = sonarr.get_series(source.tvdb_id)

    form = SourceForm(obj=source)
    form.season_choices(series.seasons)
    form.language_choices(sonarr.get_languages())
    form.quality_choices(sonarr.get_qualities())

    if request.method == "POST" and form.validate_on_submit():
        magnet, err = get_magnet(
            form.url.data, form.cookies.data, form.user_agent.data
        )
        if err:
            form.url.errors = [err]
        else:
            source.update(
                url=form.url.data,
                season=form.season.data,
                cookies=magnet.cookies,
                user_agent=magnet.user_agent or form.user_agent.data,
                quality=form.quality.data,
                language=form.language.data,
                schedule_correction=form.schedule_correction.data,
                error="",
            )
            return redirect(url_for("ui.index.index"))
    elif source.error:
        form.url.errors = [source.error]

    return render_template(
        "edit.html", form=form, series=series, source=source
    )


@bp.route("/<int:source_id>/delete", methods=["POST"])
def delete(source_id):
    Source.get(source_id).delete()
    return redirect(url_for("ui.index.index"))