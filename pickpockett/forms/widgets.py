from markupsafe import Markup
from wtforms.widgets import TextInput


class UserAgentInput(TextInput):
    def __call__(self, field, **kwargs):
        input_tag = super().__call__(field, **kwargs)
        return Markup(
            '<div class="input-group">'
            "   %s"
            "   <button %s>%s</button>"
            "</div>"
            % (
                input_tag,
                self.html_params(
                    class_="btn btn-outline-secondary",
                    type="button",
                    onclick=(
                        "getElementById('%s').value="
                        "window.navigator.userAgent" % field.id
                    ),
                ),
                "FILL",
            )
        )