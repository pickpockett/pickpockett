from pathlib import Path
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel


class GeneralConfig(BaseModel):
    user_agent: str


class FlareSolverrConfig(BaseModel):
    url: AnyHttpUrl
    timeout: int = 60000


class SonarrConfig(BaseModel):
    url: AnyHttpUrl
    apikey: str


class Config(BaseModel):
    general: Optional[GeneralConfig]
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
                self.config = Config()
        return self.config

    def save(self, obj):
        self.config = Config.parse_obj(obj)
        self.path.write_text(self.config.json())
