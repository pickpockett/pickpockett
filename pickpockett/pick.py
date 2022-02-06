import json
import re

import requests

magnet = re.compile(r"(['\"])(magnet:\?.*xt=urn:btih:[a-fA-F0-9]{40}.*?)\1")


def _prepare_cookies(cookies):
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


def find_magnet_link(url, cookies=None):
    req_cookies = _prepare_cookies(cookies) if cookies else None
    r = requests.get(url, cookies=req_cookies)
    match = magnet.search(r.text)
    if match:
        res_cookies = requests.utils.dict_from_cookiejar(r.cookies)
        return match.group(2), json.dumps(res_cookies or req_cookies)
    return None, None


def hash_from_magnet(magnet):
    pass
