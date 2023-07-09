import logging
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as et

from flask import g
from flask_sqlalchemy import BaseQuery

from .magnet import Magnet
from .models import ALL_SEASONS, Source

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


def _item(name, url, dt, magnet_url, info_hash, tvdb_id):
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
    comments.text = magnet_url

    et.SubElement(
        item,
        "enclosure",
        url=magnet_url,
        length=size_value,
        type="application/x-bittorrent;x-scheme-handler/magnet",
    )

    et.SubElement(item, "torznab:attr", name="size", value=size_value)
    et.SubElement(item, "torznab:attr", name="magneturl", value=magnet_url)
    et.SubElement(item, "torznab:attr", name="seeders", value="99")
    et.SubElement(item, "torznab:attr", name="leechers", value="0")
    et.SubElement(item, "torznab:attr", name="infohash", value=info_hash)
    if tvdb_id:
        et.SubElement(item, "torznab:attr", name="tvdbid", value=str(tvdb_id))

    return item


def _stub():
    return _item(
        "",
        "",
        datetime.utcnow(),
        "",
        "",
        None,
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
        if season:
            query = query.filter(Source.season.in_([ALL_SEASONS, season]))

    return query.all()


def _source_items(sonarr, source, season, episode):
    items = []
    series = sonarr.get_series(source.tvdb_id)
    if series is None:
        return []

    season_number = source.season if season is None else int(season)
    schedule_correction = timedelta(days=source.schedule_correction)
    dt = source.datetime + schedule_correction
    episodes = series.get_episodes(season_number, dt)

    if not episodes:
        return []

    magnet = Magnet.from_hash(source.hash, dn=series.title)

    episode_number = int(episode) if episode else None
    for ep in episodes:
        if episode_number is not None and ep.episode_number != episode_number:
            continue

        ep_name = (
            f"{series.title} S{ep.season_number:02}E{ep.episode_number:02}"
        )

        if ep.has_file:
            logger.info(
                "[tvdbid:%i]: episode exists: %s", source.tvdb_id, ep_name
            )
        else:
            logger.info(
                "[tvdbid:%i]: missing episode: %s", source.tvdb_id, ep_name
            )

        if source.version > 1:
            ep_name += f" [v{source.version}]"

        if extra := source.extra:
            ep_name += f" [{extra}]"

        item = _item(
            ep_name,
            source.url,
            source.datetime,
            magnet.url,
            magnet.hash,
            source.tvdb_id,
        )
        items.append(item)

    return items


def _get_items(q, tvdb_id, season, episode):
    if not (sonarr := g.sonarr):
        logger.warning(
            "PickPockett is not configured yet,"
            " so returning a stub to pass the Sonarr test"
        )
        return [_stub()]

    sources = _query(q, tvdb_id, season)
    items = []
    for source in sources:
        items.extend(_source_items(sonarr, source, season, episode))

    if not (q or tvdb_id or items):
        logger.info(
            "no search criteria and no items,"
            " so returning a stub to pass the Sonarr test"
        )
        return [_stub()]

    return items


def tv_search(q=None, tvdbid=None, season=None, ep=None, **_):
    items = _get_items(q, tvdbid, season, ep)

    root = et.Element(
        "rss",
        {"xmlns:torznab": "http://torznab.com/schemas/2015/feed"},
        version="2.0",
    )
    channel = et.SubElement(root, "channel")
    channel.extend(items)

    return _tostring(root)
