from flask import Blueprint, g, redirect, render_template, request, url_for

from ... import config
from ...forms.config import ConfigForm

bp = Blueprint("settings", __name__, url_prefix="/settings")


@bp.route("/", methods=["GET", "POST"])
def settings():
    conf = g.config
    form = ConfigForm(obj=conf)
    if not (conf.general.user_agent or conf.sonarr):
        form.general.form.user_agent.data = str(request.user_agent)

    if request.method == "POST" and form.validate_on_submit():
        config.save(form.data)
        return redirect(url_for("ui.index.index"))

    return render_template("settings.html", form=form)
