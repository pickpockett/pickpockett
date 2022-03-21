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


class TextAreaField(
    RequiredMixin, StripWhitespacesMixin, wtforms.TextAreaField
):
    pass


class URLField(RequiredMixin, StripWhitespacesMixin, wtforms.URLField):
    pass
