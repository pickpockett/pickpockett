import json
from typing import Dict, List, cast
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from requests.utils import dict_from_cookiejar


def _prepare_cookies(cookies):
    if cookies is None:
        return

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

    raise ValueError(f"Wrong cookie {cookies_orig!r}")


def _magnet_link(tag):
    return (
        tag.name == "a"
        and tag.has_attr("href")
        and tag["href"].startswith("magnet")
    )


def find_magnet_link(url, cookies=None):
    req_cookies = _prepare_cookies(cookies) if cookies else None

    response = requests.get(url, cookies=req_cookies)
    response.raise_for_status()

    bs = BeautifulSoup(response.text, "html.parser")
    tag = bs.find(_magnet_link)

    if tag:
        if cookies and (res_cookies := dict_from_cookiejar(response.cookies)):
            cookies = json.dumps(res_cookies)
        return tag["href"], cookies

    return None, None


def hash_from_magnet(magnet):
    url = urlparse(magnet)
    params = cast(Dict[str, List[str]], parse_qs(url.query))
    xt = params["xt"][0]
    infohash = xt.split(":")[-1]
    return infohash
