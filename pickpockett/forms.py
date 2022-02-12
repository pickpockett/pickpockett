from typing import List

from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
    SubmitField,
    TextAreaField,
    URLField,
    validators,
)

from .models import DEFAULT_QUALITY
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
        self.season.choices = (
            (-1, "All Seasons"),
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
