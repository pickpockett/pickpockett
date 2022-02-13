from pathlib import Path
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel


class SonarrConfig(BaseModel):
    url: AnyHttpUrl
    apikey: str


class Config(BaseModel):
    sonarr: SonarrConfig


class ConfigManager:
    def __init__(self, path: Path = None):
        self.path = path
        self.config: Optional[Config] = None

    def load(self):
        if not self.config and self.path.exists():
            self.config = Config.parse_file(self.path)
        return self.config

    def save(self, obj):
        self.config = Config.parse_obj(obj)
        self.path.write_text(self.config.json())
