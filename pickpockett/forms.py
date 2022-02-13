from typing import List

from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
    SubmitField,
    TextAreaField,
    URLField,
    validators,
)

from .models import ALL_SEASONS, ALL_SEASONS_NO_SPECIALS, DEFAULT_QUALITY
from .sonarr import Language, Quality, Season


def strip_filter(value: str):
    return value.strip() if isinstance(value, str) else value


class SourceForm(FlaskForm):
    url = URLField("URL", [validators.input_required()], [strip_filter])
    cookies = TextAreaField(
        "Cookies:",
        [validators.optional()],
        [strip_filter],
        description=(
            "(optional) Used for authentication."
            " The value could change between requests"
        ),
    )
    season = SelectField(
        "Season:", description="Specify which season the source contains"
    )
    quality = SelectField("Quality:", description="Quality of the source")
    language = SelectField(
        "Language:", description='(optional) Empty means "English" for Sonarr'
    )
    submit = SubmitField(render_kw={"hidden": True})

    def season_choices(self, seasons: List[Season]):
        choices = ((ALL_SEASONS, "All Seasons"),)
        for season in seasons:
            if season.season_number == 0:
                choices += (
                    (ALL_SEASONS_NO_SPECIALS, "All Seasons (w/o Specials)"),
                )
                season_title = "Specials"
            else:
                season_title = f"Season {season.season_number}"
            choices += ((season.season_number, season_title),)

        self.season.choices = choices

    def language_choices(self, languages: List[Language]):
        self.language.choices = (
            ("", ""),
            *((language.name, language.name) for language in languages),
        )

    def quality_choices(
        self, qualities: List[Quality], current: str = DEFAULT_QUALITY
    ):
        choices = [(quality.name, quality.name) for quality in qualities]
        current_quality = (current, current)
        if current_quality not in choices:
            choices.insert(0, current_quality)
        self.quality.choices = choices
