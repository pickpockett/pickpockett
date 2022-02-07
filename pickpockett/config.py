from . import db
from .models import Config


class SonarrConfig:
    _prefix = "sonarr_"

    @classmethod
    def load(cls):
        obj = cls()
        for setting in db.session.query(Config).filter(
            Config.name.startswith(cls._prefix)
        ):
            name = setting.name.split(cls._prefix, 1)[1]
            setattr(obj, name, setting.value)
        return obj
