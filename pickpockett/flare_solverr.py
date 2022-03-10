from typing import Any, Dict, List
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, validator

from . import config


class FlareSolverrSolution(BaseModel):
    cookies: Dict[str, Any]
    response: str
    user_agent: str

    class Config:
        fields = {"user_agent": "userAgent"}

    @validator("cookies", pre=True)
    def cookies_to_dict(cls, cookies: List[Dict[str, Any]]):
        return {cookie["name"]: cookie["value"] for cookie in cookies}


class FlareSolverrResponse(BaseModel):
    solution: FlareSolverrSolution


class FlareSolverr:
    def __init__(self, url):
        self.url = url

    def solve(self, url, cookies=None) -> FlareSolverrResponse:
        cookies = cookies or {}
        req_cookies = [
            {"name": key, "value": value} for key, value in cookies.items()
        ]
        headers = {"User-Agent": "PickPockett"}
        response = requests.post(
            urljoin(self.url, "v1"),
            headers=headers,
            json={"cmd": "request.get", "cookies": req_cookies, "url": url},
        )
        response.raise_for_status()
        return FlareSolverrResponse.parse_obj(response.json())


def get_flare_solverr():
    if conf_flare_solverr := config.load().flare_solverr:
        return FlareSolverr(conf_flare_solverr.url)
