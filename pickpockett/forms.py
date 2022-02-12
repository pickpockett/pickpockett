from typing import List

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, TextAreaField, validators

from .sonarr import Language, Quality, Season


class SourceForm(FlaskForm):
    url = TextAreaField("URL", validators=[validators.input_required()])
    cookies = TextAreaField(
        "Cookies:",
        description=(
            "(optional) Used for authentication."
            " The value could change between requests"
        ),
        validators=[validators.optional()],
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

    def quality_choices(self, current: str, qualities: List[Quality]):
        current_quality = (current, current)
        choices = [(quality.name, quality.name) for quality in qualities]
        if current_quality not in choices:
            choices.insert(0, current_quality)
        self.quality.choices = choices
