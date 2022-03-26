from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, validator


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
    def __init__(self, flaresolverr_config):
        self.url = flaresolverr_config.url
        self.timeout = flaresolverr_config.timeout
        self._session = None

    def _post(self, data):
        headers = {"User-Agent": "PickPockett"}
        response = requests.post(
            urljoin(self.url, "v1"),
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    @property
    def session(self):
        if self._session is None:
            self._session = str(datetime.utcnow())
            data = {
                "cmd": "sessions.create",
                "maxTimeout": self.timeout,
                "session": self._session,
            }
            self._post(data)
        return self._session

    def solve(self, url, cookies=None) -> FlareSolverrResponse:
        cookies = cookies or {}
        req_cookies = [
            {"name": key, "value": value} for key, value in cookies.items()
        ]
        data = {
            "cmd": "request.get",
            "cookies": req_cookies,
            "session": self.session,
            "url": url,
        }

        response = self._post(data)
        return FlareSolverrResponse.parse_obj(response)

    def destroy(self):
        if self._session is not None:
            data = {"cmd": "sessions.destroy", "session": self._session}
            self._post(data)
