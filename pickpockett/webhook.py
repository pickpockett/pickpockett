import requests


class WebHook:
    def __init__(self, url: str) -> None:
        self.url = url

    def hook(self, old: str, new: str) -> None:
        requests.get(self.url, params={"old": old, "new": new})
