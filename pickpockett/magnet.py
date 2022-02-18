import json
import logging
from typing import Dict, List, Optional, cast
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from requests.utils import dict_from_cookiejar

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


def _prepare_cookies(cookies):
    if not cookies:
        return None

    cookies_orig = cookies

    if isinstance(cookies, str):
        try:
            cookies = json.loads(cookies)
        except json.JSONDecodeError:
            return {
                k: v
                for k, _, v in (
                    s.strip().partition("=") for s in cookies.split(";")
                )
            }

    if isinstance(cookies, dict):
        return cookies

    if isinstance(cookies, list):
        return {c["name"]: c["value"] for c in cookies}

    raise ValueError(f"Wrong cookies {cookies_orig!r}")


def _magnet_link(tag):
    return (
        tag.name == "a"
        and tag.has_attr("href")
        and tag["href"].startswith("magnet")
    )


def _find_magnet_link(url, cookies) -> Optional[Magnet]:
    req_cookies = _prepare_cookies(cookies)

    response = requests.get(url, cookies=req_cookies, timeout=5)
    response.raise_for_status()

    bs = BeautifulSoup(response.text, "html.parser")
    tag = bs.find(_magnet_link)

    if tag:
        if cookies and (res_cookies := dict_from_cookiejar(response.cookies)):
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
