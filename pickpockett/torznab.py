import time
from datetime import datetime
from typing import List
from xml.etree import ElementTree as et

import tzlocal

from .db import Session, Source
from .pick import find_magnet_link, hash_from_magnet
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

    searching = et.SubElement(root, "searching")
    et.SubElement(searching, "search", available="yes", supportedParams="q")
    et.SubElement(
        searching, "tv-search", available="yes", supportedParams="q,season,ep"
    )
    et.SubElement(
        searching, "movie-search", available="no", supportedParams="q"
    )

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


def _item(name, url, timestamp, magneturl, infohash, tvdb_id):
    size_value = "0"

    item = et.Element("item")

    title = et.SubElement(item, "title")
    title.text = name

    guid = et.SubElement(item, "guid")
    guid.text = name

    comments = et.SubElement(item, "comments")
    comments.text = url

    pub_date = et.SubElement(item, "pubDate")
    pub_date.text = _rss_date(timestamp)

    size = et.SubElement(item, "size")
    size.text = size_value

    description = et.SubElement(item, "description")
    description.text = title

    comments = et.SubElement(item, "link")
    comments.text = magneturl

    et.SubElement(
        item,
        "enclosure",
        url=magneturl,
        length=size_value,
        type="application/x-bittorrent;x-scheme-handler/magnet",
    )

    et.SubElement(item, "torznab:attr", name="size", value=size_value)
    et.SubElement(item, "torznab:attr", name="magneturl", value=magneturl)
    et.SubElement(item, "torznab:attr", name="seeders", value="99")
    et.SubElement(item, "torznab:attr", name="leechers", value="0")
    et.SubElement(item, "torznab:attr", name="infohash", value=infohash)
    if tvdb_id:
        et.SubElement(item, "torznab:attr", name="tvdbid", value=str(tvdb_id))

    return item


def _stub():
    return [
        _item(
            "pickpockett",
            "https://github.com/pickpockett/pickpockett",
            time.time(),
            "magnet:?xt=urn:btih:",
            "",
            0,
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

            magnetlink, cookies = find_magnet_link(source.link, source.cookies)
            if magnetlink is None:
                continue

            infohash = hash_from_magnet(magnetlink)
            if source.hash != infohash:
                source.hash = infohash
                source.timestamp = time.time()
                session.merge(source)
                session.commit()

            if cookies:
                source.cookies = cookies
                session.merge(source)
                session.commit()

            season = source.season or 1
            tvdb_id = get_tvdb_id(source.title, sonarr)
            for i in range(1, 100):
                item = _item(
                    source.title + f" S{season:02}E{i:02} (1080p WEBRip)",
                    source.link,
                    source.timestamp,
                    magnetlink,
                    infohash,
                    tvdb_id,
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
