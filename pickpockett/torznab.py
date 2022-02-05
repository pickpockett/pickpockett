import time
from datetime import datetime
from xml.etree import ElementTree as et

import tzlocal

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


def _item(name, url, magnet, timestamp):
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

    return item


def _tostring(xml):
    return et.tostring(xml, encoding="utf-8", xml_declaration=True)


def tv_search(q=None, **_):
    if True:
        items = [
            _item(
                "test",
                "https://github.com/pickpockett/pickpockett",
                "magnet:?xt=urn:btih:",
                time.time(),
            )
        ]

    root = et.Element("rss", version="2.0")
    channel = et.SubElement(root, "channel")

    for item in items:
        channel.append(item)

    return _tostring(root)
