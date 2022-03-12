import json
import logging
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup

from . import config
from .flaresolverr import FlareSolverr

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


def _get_page(url, cookies, user_agent):
    req_cookies = _prepare_cookies(cookies)
    conf = config.load()
    headers = {
        **HEADERS,
        "Referer": url,
    }
    if not user_agent and conf.general and conf.general.user_agent:
        user_agent = conf.general.user_agent
    if user_agent:
        headers["User-Agent"] = user_agent

    response = requests.get(
        url, cookies=req_cookies, headers=headers, timeout=5
    )
    if (
        response.status_code >= HTTPStatus.BAD_REQUEST
        and conf.flaresolverr
        and conf.flaresolverr.url
    ):
        flaresolverr = FlareSolverr(conf.flaresolverr)
        try:
            solution = flaresolverr.solve(url, req_cookies).solution
        except Exception as e:
            logger.error(e)
        else:
            logger.info("challenge solved: %s", url)
            new_cookies = {**req_cookies, **solution.cookies}
            return solution.response, new_cookies, solution.user_agent

    response.raise_for_status()
    new_cookies = {**req_cookies, **response.cookies.get_dict()}
    return response.text, new_cookies, ""


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
    except Exception as e:
        logger.error(e)
        raise ParseError("Unknown Error")

    bs = BeautifulSoup(text, "html.parser")
    return bs, cookies, user_agent
