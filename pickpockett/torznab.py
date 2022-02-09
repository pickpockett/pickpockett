import logging
from datetime import datetime, timezone
from xml.etree import ElementTree as et

from flask_sqlalchemy import BaseQuery

from . import db
from .config import SonarrConfig
from .models import Source
from .pick import find_magnet_link, hash_from_magnet
from .sonarr import Sonarr

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


logger = logging.getLogger(__name__)


def error(code, description):
    root = et.Element("error", code=str(code), description=description)
    return _tostring(root)


def _search(name="search", *, available=True, params="q"):
    return et.Element(
        name, available="yes" if available else "no", supportedParams=params
    )


def caps(**_):
    root = et.Element("caps")

    searching = et.SubElement(root, "searching")
    searching.append(_search())
    searching.append(_search("tv-search", params="tvdbid,season,ep"))
    searching.append(_search("movie-search", available=False))

    categories = et.SubElement(root, "categories")
    category = et.SubElement(categories, "category", id="5000", name="TV")
    et.SubElement(category, "subcat", id="5030", name="SD")
    et.SubElement(category, "subcat", id="5040", name="HD")

    return _tostring(root)


def _rss_date(dt):
    dt = dt.replace(tzinfo=timezone.utc)
    rss_date = dt.strftime("%a, %d %b %Y %H:%M:%S %z")
    return rss_date


def _item(name, url, dt, magneturl, infohash, tvdb_id):
    size_value = "0"

    item = et.Element("item")

    title = et.SubElement(item, "title")
    title.text = name

    guid = et.SubElement(item, "guid")
    guid.text = name

    comments = et.SubElement(item, "comments")
    comments.text = url

    pub_date = et.SubElement(item, "pubDate")
    pub_date.text = _rss_date(dt)

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
    return _item(
        "pickpockett",
        "https://github.com/pickpockett/pickpockett",
        datetime.utcnow(),
        "magnet:?xt=urn:btih:",
        "",
        0,
    )


def _tostring(xml):
    return et.tostring(xml, encoding="utf-8", xml_declaration=True)


def _query(q, tvdb_id, season):
    if q:
        logger.info("'q' search parameter isn't supported")
        return []

    query: BaseQuery = Source.query

    if tvdb_id:
        query = query.filter_by(tvdb_id=tvdb_id)
        if not db.session.query(query.exists()).scalar():
            source = Source(tvdb_id=tvdb_id)
            db.session.add(source)
            db.session.commit()

        if season:
            query = query.filter_by(season=season)

    return query.all()


def tv_search(q=None, tvdbid=None, season=None, **_):
    items = []
    sources = _query(q, tvdbid, season)

    for source in sources:
        if not source.link:
            continue

        magnet_link, cookies = find_magnet_link(source.link, source.cookies)
        if magnet_link is None:
            logger.info(
                "[tvdbid:%i]: no magnet: %r", source.tvdb_id, source.link
            )
            continue

        info_hash = hash_from_magnet(magnet_link)
        if source.hash != info_hash:
            logger.info(
                "[tbdbid:%i]: update hash: %r => %r",
                source.tvdb_id,
                source.hash,
                info_hash,
            )
            source.hash = info_hash
            source.datetime = datetime.utcnow()
            db.session.commit()

        if cookies:
            source.cookies = cookies
            db.session.commit()

        sonarr_config = SonarrConfig()
        sonarr = Sonarr(sonarr_config)

        title, missing = sonarr.get_missing(
            source.tvdb_id, source.season, source.datetime
        )

        for ep in missing:
            episode = f"{title} S{ep.season_number:02}E{ep.episode_number:02}"
            logger.info(
                "[tvdb:%i]: missing episode: %s", source.tvdb_id, episode
            )
            name = f"{episode} [1080p WEBRip]"
            item = _item(
                name,
                source.link,
                source.datetime,
                magnet_link,
                info_hash,
                tvdbid,
            )
            items.append(item)

    if not (q or tvdbid or sources):
        logger.info("no search criteria and no sources, so return a stub")
        items.append(_stub())

    root = et.Element(
        "rss",
        {"xmlns:torznab": "http://torznab.com/schemas/2015/feed"},
        version="2.0",
    )
    channel = et.SubElement(root, "channel")
    channel.extend(items)

    return _tostring(root)
