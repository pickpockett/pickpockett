from flask_wtf import FlaskForm
from wtforms import FormField, IntegerField, SubmitField, validators
from wtforms.widgets import NumberInput

from .fields import StringField, URLField
from .widgets import UserAgentInput


class GeneralConfigForm(FlaskForm):
    check_interval = IntegerField(
        "Check interval (min)", [validators.number_range(min=1)]
    )
    user_agent = StringField(
        "Default User Agent", required=True, widget=UserAgentInput()
    )


class FlareSolverrForm(FlaskForm):
    url = URLField("URL", required=False, description="optional")
    timeout = IntegerField(
        "Timeout (ms)",
        [validators.number_range(min=0)],
        widget=NumberInput(step=1000),
    )


class SonarrConfigForm(FlaskForm):
    url = URLField("URL", required=True)
    apikey = StringField("API Key", required=True)


class ConfigForm(FlaskForm):
    general = FormField(GeneralConfigForm, "General")
    sonarr = FormField(SonarrConfigForm, "Sonarr")
    flaresolverr = FormField(FlareSolverrForm, "FlareSolverr")
    submit = SubmitField(render_kw={"hidden": True})
