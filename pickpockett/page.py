import json

import requests
from bs4 import BeautifulSoup


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


def parse(url, cookies):
    req_cookies = _prepare_cookies(cookies)

    response = requests.get(url, cookies=req_cookies, timeout=5)
    response.raise_for_status()

    bs = BeautifulSoup(response.text, "html.parser")
    bs.cookies = response.cookies
    return bs
