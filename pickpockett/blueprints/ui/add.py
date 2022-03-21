from flask import Blueprint, redirect, render_template, request, url_for

from ...forms import GuessForm, SourceForm
from ...magnet import get_magnet
from ...models import Source
from ...sonarr import get_sonarr

bp = Blueprint("add", __name__, url_prefix="/add")


@bp.route("/")
def add():
    args = request.args.copy()
    tvdb_ids = list(map(int, args.poplist("tvdb_id")))
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings.settings"))

    series = sonarr.series()
    if tvdb_ids:
        series = [s for s in series if s.tvdb_id in tvdb_ids]
    return render_template("add.html", series=series, args=args)


@bp.route("/<int:tvdb_id>", methods=["GET", "POST"])
def add_source(tvdb_id):
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings.settings"))

    series = sonarr.get_series(tvdb_id)

    form = SourceForm(**request.args)
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
            Source.create(
                tvdb_id=tvdb_id,
                url=form.url.data,
                season=form.season.data,
                cookies=magnet.cookies,
                user_agent=magnet.user_agent or form.user_agent.data,
                quality=form.quality.data,
                language=form.language.data,
                schedule_correction=form.schedule_correction.data,
            )
            return redirect(url_for("ui.index.index"))
    elif form.season.data is None or form.season.data > series.season_count:
        form.season.data = series.seasons[-1].season_number

    return render_template("add_source.html", form=form, series=series)


@bp.route("/smart", methods=["GET", "POST"])
def add_smart():
    if (sonarr := get_sonarr()) is None:
        return redirect(url_for("ui.settings.settings"))

    form = GuessForm()

    if request.method == "POST" and form.validate_on_submit():
        magnet, err = get_magnet(
            form.url.data, form.cookies.data, form.user_agent.data
        )
        if err:
            form.url.errors = [err]
        else:
            args = {k: v for k, v in form.data.items() if k != "submit" and v}
            if magnet.cookies:
                args["cookies"] = magnet.cookies
            if user_agent := (magnet.user_agent or form.user_agent.data):
                args["user_agent"] = user_agent

            if (tag := magnet.page.find("title")) and (
                lookup := sonarr.series_lookup(tag.text)
            ):
                if parsed := (
                    sonarr.parse(tag.text)
                    or sonarr.parse(tag.text, strip=True)
                ):
                    if parsed.season_number > 0:
                        args["season"] = parsed.season_number
                    if parsed.quality.quality.name != "Unknown":
                        args["quality"] = parsed.quality.quality.name
                    if parsed.language.name != "English":
                        args["language"] = parsed.language.name
                if len(lookup) == 1:
                    return redirect(
                        url_for(
                            "ui.add.add_source",
                            tvdb_id=lookup[0].tvdb_id,
                            **args,
                        )
                    )
                else:
                    args["tvdb_id"] = [series.tvdb_id for series in lookup]

            return redirect(url_for("ui.add.add", **args))

    return render_template("add_smart.html", form=form)
