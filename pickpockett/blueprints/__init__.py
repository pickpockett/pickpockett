from flask import g

from .. import config
from ..flaresolverr import FlareSolverr
from ..sonarr import Sonarr
from . import api, ui


@api.bp.before_request
@ui.bp.before_request
def before_request():
    g.config = config.load()
    g.sonarr = Sonarr(g.config.sonarr) if g.config.sonarr else None
    g.flaresolverr = (
        FlareSolverr(g.config.flaresolverr)
        if g.config.flaresolverr and g.config.flaresolverr.url
        else None
    )


@api.bp.after_request
@ui.bp.after_request
def after_request(response):
    try:
        g.flaresolverr.destroy()
    except Exception:
        pass

    return response
