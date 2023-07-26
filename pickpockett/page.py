import json
import logging

import requests
from bs4 import BeautifulSoup
from flask import g

logger = logging.getLogger(__name__)


def _prepare_cookies(cookies):
    if not cookies:
        return {}

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


HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;"
        "q=0.8,application/signed-exchange;v=b3;q=0.9"
    ),
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,uk;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
}


def _prep_headers_and_cookies(url, cookies, user_agent):
    conf = g.config
    if not user_agent and conf.general.user_agent:
        user_agent = conf.general.user_agent

    headers = {
        **HEADERS,
        "Referer": url,
    }
    if user_agent:
        headers["User-Agent"] = user_agent

    cookies = _prepare_cookies(cookies)
    return headers, cookies


def _get_page(url, cookies, user_agent):
    headers, cookies = _prep_headers_and_cookies(url, cookies, user_agent)
    response = requests.get(url, cookies=cookies, headers=headers, timeout=5)
    cookies.update(response.cookies.get_dict())
    if 400 <= response.status_code < 500 and g.flaresolverr:
        try:
            solution = g.flaresolverr.solve(url, cookies).solution
        except Exception as e:
            logger.error(e)
        else:
            logger.info("challenge solved: %s", url)
            cookies.update(solution.cookies)
            return solution.response, cookies, solution.user_agent

    response.raise_for_status()
    return response.text, cookies, ""


def parse(url, cookies, user_agent):
    try:
        text, cookies, user_agent = _get_page(url, cookies, user_agent)
    except requests.HTTPError as e:
        logger.error(e)
        if e.response is not None:
            raise ParseError(
                e.response.reason or f"Error {e.response.status_code}"
            )
        raise ParseError("HTTP Error")
    except requests.ConnectionError as e:
        logger.error(e)
        raise ParseError("Connection Error")
    except requests.Timeout as e:
        logger.error(e)
        raise ParseError("Timeout Error")
    except requests.RequestException as e:
        logger.error(e)
        raise ParseError("Request Error")
    except ValueError as e:
        logger.error(e)
        raise ParseError("Cookies parse error")
    except Exception as e:
        logger.error(e)
        raise ParseError("Unknown Error")

    bs = BeautifulSoup(text, "html.parser")
    return bs, cookies, user_agent


def get_torrent(url, cookies, user_agent):
    headers, cookies = _prep_headers_and_cookies(url, cookies, user_agent)
    response = requests.get(url, cookies=cookies, headers=headers, timeout=5)
    if response.headers.get("content-type") == "application/x-bittorrent":
        return response.content
