import json
import logging
from typing import Dict, List, Optional, cast
from urllib.parse import parse_qs, urlparse

from .page import ParseError, parse

logger = logging.getLogger(__name__)


class Magnet:
    def __init__(self, url, cookies="", user_agent=""):
        self.url = url
        self.cookies = cookies
        self.user_agent = user_agent
        self._hash = None

    @property
    def hash(self):
        if self._hash is None or self._hash not in self.url:
            self._hash = _hash_from_magnet(self.url)

        return self._hash


def _magnet_link(tag):
    return (
        tag.name == "a"
        and tag.has_attr("href")
        and tag["href"].startswith("magnet")
    )


def _find_magnet_link(url, cookies, user_agent) -> Optional[Magnet]:
    page, page_cookies, user_agent = parse(url, cookies, user_agent)
    if tag := page.find(_magnet_link):
        if (cookies or user_agent) and page_cookies:
            cookies = json.dumps(page_cookies)
        return Magnet(tag["href"], cookies, user_agent)

    return Magnet(None)


def _hash_from_magnet(magnet_url):
    url = urlparse(magnet_url)
    params = cast(Dict[str, List[str]], parse_qs(url.query))
    xt = params["xt"][0]
    infohash = xt.split(":")[-1]
    return infohash


def get_magnet(url, cookies, user_agent):
    try:
        magnet = _find_magnet_link(url, cookies, user_agent)
    except ParseError as e:
        return None, str(e)

    error = "No magnet link found" if magnet.url is None else None

    return magnet, error
