from typing import List

from flask_wtf import FlaskForm
from wtforms import (
    FormField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    URLField,
    validators,
)

from .models import ALL_SEASONS, DEFAULT_QUALITY
from .sonarr import Language, Quality, Season


def strip_filter(value: str):
    return value.strip() if isinstance(value, str) else value


class SourceForm(FlaskForm):
    url = URLField("URL", [validators.input_required()], [strip_filter])
    cookies = TextAreaField(
        "Cookies",
        [validators.optional()],
        [strip_filter],
        description=(
            "(optional) Used for authentication."
            " The value could change between requests"
        ),
    )
    season = SelectField(
        "Season",
        coerce=int,
        description="Specify which season the source contains",
    )
    quality = SelectField(
        "Quality", default=DEFAULT_QUALITY, description="Quality of the source"
    )
    language = SelectField(
        "Language", description='(optional) Empty means "English" to Sonarr'
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
        self.season.data = seasons[-1].season_number

    def language_choices(self, languages: List[Language]):
        self.language.choices = (
            ("", ""),
            *((language.name, language.name) for language in languages),
        )

    def quality_choices(self, qualities: List[Quality]):
        choices = [(quality.name, quality.name) for quality in qualities]
        current_quality = (self.quality.data, self.quality.data)
        if current_quality not in choices:
            choices.insert(0, current_quality)
        self.quality.choices = choices


class SonarrConfigForm(FlaskForm):
    url = URLField("URL", [validators.input_required()], [strip_filter])
    apikey = StringField(
        "API Key", [validators.input_required()], [strip_filter]
    )


class ConfigForm(FlaskForm):
    sonarr = FormField(SonarrConfigForm)
    submit = SubmitField(render_kw={"hidden": True})
