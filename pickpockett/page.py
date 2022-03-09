import json
import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


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


class ParseError(Exception):
    pass


def parse(url, cookies):
    req_cookies = _prepare_cookies(cookies)

    try:
        response = requests.get(url, cookies=req_cookies, timeout=5)
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.error(e)
        if e.response is not None:
            raise ParseError(
                e.response.reason or f"Error {e.response.status_code}"
            )
        return ParseError("HTTP Error")
    except requests.ConnectionError as e:
        logger.error(e)
        return ParseError("Connection Error")
    except requests.RequestException as e:
        logger.error(e)
        return ParseError("Request Error")
    except Exception as e:
        logger.error(e)
        return ParseError("Unknown Error")

    bs = BeautifulSoup(response.text, "html.parser")
    bs.cookies = response.cookies
    return bs
