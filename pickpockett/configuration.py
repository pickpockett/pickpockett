from pathlib import Path
from typing import Literal, Optional, Union

from pydantic import AnyHttpUrl, BaseModel


class GeneralConfig(BaseModel):
    check_interval: int = 15
    user_agent: str = ""


class FlareSolverrConfig(BaseModel):
    url: Union[AnyHttpUrl, Literal[""]]
    timeout: int = 60000


class SonarrConfig(BaseModel):
    url: AnyHttpUrl
    apikey: str


class WebHook(BaseModel):
    url: Union[AnyHttpUrl, Literal[""]]


class Config(BaseModel):
    general: GeneralConfig
    sonarr: Optional[SonarrConfig] = None
    flaresolverr: Optional[FlareSolverrConfig] = None
    webhook: Optional[WebHook] = None


class ConfigManager:
    def __init__(self, path: Path = None):
        self.path = path
        self.config: Optional[Config] = None

    def load(self):
        if self.config is None:
            if self.path.exists():
                self.config = Config.model_validate_json(self.path.read_text())
            else:
                self.config = Config(general=GeneralConfig())
        return self.config

    def save(self, obj):
        from .scheduler import reschedule

        self.config = Config.model_validate(obj)
        self.path.write_text(self.config.model_dump_json())

        reschedule(self.config)
