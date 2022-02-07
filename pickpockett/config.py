from .models import Config


class ConfigParameter:
    def __get__(self, instance, owner=None):
        if parameter := Config.query.get(self._name):
            return parameter.value

    def __set_name__(self, owner, name):
        prefix = owner.__name__.rstrip("Config").lower()
        self._name = prefix + "_" + name


class SonarrConfig:
    url = ConfigParameter()
    apikey = ConfigParameter()
