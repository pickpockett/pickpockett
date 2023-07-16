import hashlib
import logging
import re
from typing import Dict, List, Optional, cast
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import pyben

from .page import ParseError, get_torrent, parse

logger = logging.getLogger(__name__)


class Magnet:
    def __init__(self, url, page=None, cookies=None, user_agent=""):
        self.url = url
        self.page = page
        self.cookies = cookies or {}
        self.user_agent = user_agent
        self._hash = None

    @property
    def hash(self):
        if self._hash is None or self._hash not in self.url:
            self._hash = _hash_from_magnet(self.url)

        return self._hash

    @classmethod
    def from_hash(cls, hsh, **kwargs):
        params = {"xt": [f"urn:btih:{hsh}"]}
        for key, value in kwargs.items():
            params[key] = [value]
        query = _make_query(params)
        url = urlunparse(["magnet", "", "", "", query, ""])
        return cls(url)


def _make_query(params):
    return urlencode(params, doseq=True, safe=":/")


def _find_magnet_link(url, cookies, user_agent) -> Optional[Magnet]:
    page, page_cookies, user_agent = parse(url, cookies, user_agent)
    if (cookies or user_agent) and page_cookies:
        cookies = page_cookies

    if tag := page.find("a", href=re.compile("^magnet:")):
        return Magnet(tag["href"], page, cookies, user_agent)

    elif download_url := page.find(
        "a", href=re.compile(r"^(?!#).*(download|dl\.php)")
    ):
        download_url = urljoin(url, download_url["href"])
        try:
            torrent = get_torrent(download_url, cookies, user_agent)
        except Exception as e:
            logger.error(e)
        else:
            if torrent:
                meta = pyben.loads(torrent)
                info = meta["info"]
                sha = hashlib.sha1(pyben.dumps(info))
                magnet_hash = sha.hexdigest()
                params = {"xt": [f"urn:btih:{magnet_hash}"]}
                query = _make_query(params)
                magnet_link = urlunparse(["magnet", "", "", "", query, ""])
                return Magnet(magnet_link, page, cookies, user_agent)

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
        return None, repr(e)

    error = "No magnet link found" if magnet.url is None else None

    return magnet, error
