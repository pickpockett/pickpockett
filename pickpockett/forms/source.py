from typing import List

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField, validators
from wtforms.widgets import TextArea

from ..models import ALL_SEASONS, DEFAULT_QUALITY
from ..sonarr import Season
from .fields import JSONField, StringField, TextAreaField, URLField
from .widgets import UserAgentInput


class SourceForm(FlaskForm):

    url = URLField(
        "URL",
        required=True,
        description="Where to find a magnet link",
        widget=TextArea(),
    )
    season = SelectField(
        "Season",
        coerce=int,
        description="Specify what season the source contains",
    )
    quality = SelectField(
        "Quality",
        default=DEFAULT_QUALITY,
        description=(
            "Quality of the source. Might not match the source"
            " but must match the quality profile of the show in Sonarr"
        ),
    )
    language = SelectField(
        "Language", description='(optional) Empty means "English" to Sonarr'
    )
    schedule_correction = IntegerField(
        "Schedule correction (days)",
        [validators.number_range(min=0)],
        default=0,
        description="Time delta between release date and air date",
    )
    cookies = JSONField(
        "Cookies",
        description=(
            "(optional) Used for authentication."
            " The value can change between requests."
            ' Here is an <a href="https://chrome.google.com/webstore/detail'
            '/copy-cookies/jcbpglbplpblnagieibnemmkiamekcdg">extension</a>'
            " to copy cookies of a web page"
        ),
    )
    user_agent = StringField(
        "User Agent",
        required=False,
        description="(optional) Could be helpful to bypass Cloudflare",
        widget=UserAgentInput(),
    )
    submit = SubmitField(render_kw={"hidden": True})

    def season_choices(self, seasons: List[Season]):
        self.season.choices = (
            (ALL_SEASONS, "All Seasons"),
            *(
                (
                    s.season_number,
                    f"Season {s.season_number}"
                    if s.season_number
                    else "Specials",
                )
                for s in seasons
            ),
        )

    def language_choices(self, languages: List[str]):
        self.language.choices = (
            ("", ""),
            *((language, language) for language in languages),
        )

    def quality_choices(self, qualities: List[str]):
        choices = [(quality, quality) for quality in qualities]
        current_quality = (self.quality.data, self.quality.data)
        if current_quality not in choices:
            choices.insert(0, current_quality)
        self.quality.choices = choices


class GuessForm(FlaskForm):
    url = URLField(
        "URL",
        required=True,
        description="Guess a series from this link",
        widget=TextArea(),
    )
    cookies = TextAreaField(
        "Cookies",
        required=False,
        description=(
            "(optional) Used for authentication."
            ' Here is an <a href="https://chrome.google.com/webstore/detail'
            '/copy-cookies/jcbpglbplpblnagieibnemmkiamekcdg">extension</a>'
            " to copy cookies of a web page"
        ),
    )
    user_agent = StringField(
        "User Agent",
        required=False,
        description="(optional) Could be helpful to bypass Cloudflare",
        widget=UserAgentInput(),
    )
    submit = SubmitField(render_kw={"hidden": True})
