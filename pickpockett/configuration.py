from pathlib import Path
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel


class GeneralConfig(BaseModel):
    check_interval: int = 15
    user_agent: str = ""


class OptionalHttpUrl(AnyHttpUrl):
    @classmethod
    def validate(cls, value, field, config):
        if value:
            return super().validate(value, field, config)
        return ""


class FlareSolverrConfig(BaseModel):
    url: OptionalHttpUrl
    timeout: int = 60000


class SonarrConfig(BaseModel):
    url: AnyHttpUrl
    apikey: str


class Config(BaseModel):
    general: GeneralConfig
    sonarr: Optional[SonarrConfig]
    flaresolverr: Optional[FlareSolverrConfig]


class ConfigManager:
    def __init__(self, path: Path = None):
        self.path = path
        self.config: Optional[Config] = None

    def load(self):
        if self.config is None:
            if self.path.exists():
                self.config = Config.parse_file(self.path)
            else:
                self.config = Config(general=GeneralConfig())
        return self.config

    def save(self, obj):
        from .scheduler import reschedule

        self.config = Config.parse_obj(obj)
        self.path.write_text(self.config.json())

        reschedule(self.config)
