import time
from datetime import datetime
from typing import List
from xml.etree import ElementTree as et

import tzlocal

from .db import Session, Source
from .pick import find_magnet_link
from .sonarr import Sonarr, get_tvdb_id

CAPS = "caps"
REGISTER = "register"
SEARCH = "search"
TV_SEARCH = "tvsearch"
MOVIE_SEARCH = "movie"
MUSIC_SEARCH = "music"
BOOK_SEARCH = "book"
DETAILS = "details"
GETNFO = "getnfo"
GET = "get"
CART_ADD = "cartadd"
CART_DEL = "cartdel"
COMMENTS = "comments"
COMMENTS_ADD = "commentadd"
USER = "user"
NZB_ADD = "nzbadd"


def error(code, description):
    root = et.Element("error", code=str(code), description=description)
    return _tostring(root)


def caps(**_):
    root = et.Element("caps")

    categories = et.SubElement(root, "categories")
    category = et.SubElement(categories, "category", id="5000", name="TV")
    et.SubElement(category, "subcat", id="5030", name="SD")
    et.SubElement(category, "subcat", id="5040", name="HD")

    return _tostring(root)


def _rss_date(timestamp):
    tz = tzlocal.get_localzone()
    dt = datetime.fromtimestamp(timestamp, tz)
    rss_date = dt.strftime("%a, %d %b %Y %H:%M:%S %z")
    return rss_date


def _item(name, tvdb_id, url, magnet, timestamp):
    item = et.Element("item")

    title = et.SubElement(item, "title")
    title.text = name

    guid = et.SubElement(item, "guid")
    guid.text = url

    pub_date = et.SubElement(item, "pubDate")
    pub_date.text = _rss_date(timestamp)

    comments = et.SubElement(item, "comments")
    comments.text = url

    et.SubElement(
        item,
        "enclosure",
        url=magnet,
        length="0",
        type="application/x-bittorrent;x-scheme-handler/magnet",
    )

    if tvdb_id:
        et.SubElement(item, "torznab:attr", name="tvdbid", value=str(tvdb_id))

    return item


def _stub():
    return [
        _item(
            "pickpockett",
            0,
            "https://github.com/pickpockett/pickpockett",
            "magnet:?xt=urn:btih:",
            time.time(),
        )
    ]


def _tostring(xml):
    return et.tostring(xml, encoding="utf-8", xml_declaration=True)


def tv_search(q=None, **_):
    items = []

    session = Session()
    if q:
        sources: List[Source] = list(session.query(Source).filter_by(title=q))

        if not sources:
            source = Source(title=q)
            session.merge(source)
            session.commit()
    else:
        sources: List[Source] = list(session.query(Source))

        if not sources:
            items.append(_stub())

    if sources:
        sonarr = Sonarr.load(session)

        for source in sources:
            if not source.link:
                continue

            magnet, cookies = find_magnet_link(source.link, source.cookies)
            if magnet is None:
                continue

            source.cookies = cookies
            session.merge(source)
            session.commit()

            item = _item(
                source.title + f" S{source.season or 1}E1-99",
                get_tvdb_id(source.title, sonarr),
                source.link,
                magnet,
                time.time(),
            )
            items.append(item)

    root = et.Element(
        "rss",
        {"xmlns:torznab": "http://torznab.com/schemas/2015/feed"},
        version="2.0",
    )
    channel = et.SubElement(root, "channel")

    for item in items:
        channel.append(item)

    return _tostring(root)
