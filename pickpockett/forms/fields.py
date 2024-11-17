import json

import wtforms


def strip_whitespaces(value: str):
    return value.strip() if isinstance(value, str) else value


class RequiredMixin:
    def __init__(self, *args, required=None, **kwargs):
        validators = None
        if required is True:
            validators = [wtforms.validators.input_required()]
        elif required is False:
            validators = [wtforms.validators.optional()]

        super().__init__(*args, validators=validators, **kwargs)


class StripWhitespacesMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, filters=[strip_whitespaces], **kwargs)


class StringField(RequiredMixin, StripWhitespacesMixin, wtforms.StringField):
    pass


class URLField(RequiredMixin, StripWhitespacesMixin, wtforms.URLField):
    pass


def _prepare_cookies(cookies):
    if not cookies:
        return {}

    cookies_orig = cookies

    if isinstance(cookies, str):
        try:
            cookies = json.loads(cookies)
        except json.JSONDecodeError:
            return {
                k: v
                for k, _, v in (
                    s.strip().partition("=") for s in cookies.split(";")
                )
            }

    if isinstance(cookies, dict):
        return cookies.copy()

    if isinstance(cookies, list):
        return {c["name"]: c["value"] for c in cookies}

    raise ValueError(f"Wrong cookies {cookies_orig!r}")


class CookiesField(wtforms.TextAreaField):
    def process_formdata(self, valuelist):
        value = _prepare_cookies(valuelist[0])
        super().process_formdata([value])

    def process_data(self, value):
        value = _prepare_cookies(value)
        super().process_data(value)

    def _value(self):
        return json.dumps(self.data) if self.data else ""
