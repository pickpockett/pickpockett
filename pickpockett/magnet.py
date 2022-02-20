import json
import logging
from typing import Dict, List, Optional, cast
from urllib.parse import parse_qs, urlparse

import requests
from requests.utils import dict_from_cookiejar

from .page import parse

logger = logging.getLogger(__name__)


class Magnet:
    def __init__(self, url, cookies=""):
        self.url = url
        self.cookies = cookies
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


def _find_magnet_link(url, cookies) -> Optional[Magnet]:
    page = parse(url, cookies)
    if tag := page.find(_magnet_link):
        if cookies and (res_cookies := dict_from_cookiejar(page.cookies)):
            cookies = json.dumps(res_cookies)
        return Magnet(tag["href"], cookies)

    return Magnet(None)


def _hash_from_magnet(magnet_url):
    url = urlparse(magnet_url)
    params = cast(Dict[str, List[str]], parse_qs(url.query))
    xt = params["xt"][0]
    infohash = xt.split(":")[-1]
    return infohash


def get_magnet(url, cookies=""):
    try:
        magnet = _find_magnet_link(url, cookies)
    except requests.HTTPError as e:
        logger.error(e)
        if e.response is not None:
            return None, e.response.reason
        return None, "HTTP Error"
    except requests.ConnectionError as e:
        logger.error(e)
        return None, "Connection Error"
    except requests.RequestException as e:
        logger.error(e)
        return None, "Request Error"
    except Exception as e:
        logger.error(e)
        return None, "Unknown Error"

    error = "No magnet link found" if magnet.url is None else None

    return magnet, error
