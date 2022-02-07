from flask import Response, request

from . import app, db, torznab


@app.route("/")
def ui():
    return "soon..."


@app.route("/api")
def api():
    kwargs = request.args.copy()
    t = kwargs.pop("t", None)

    if t == torznab.CAPS:
        caps = torznab.caps(**kwargs)
        return Response(caps)
    elif t in (torznab.SEARCH, torznab.TV_SEARCH):
        search = torznab.tv_search(**kwargs)
        return Response(search)
    elif t in (
        torznab.REGISTER,
        torznab.MOVIE_SEARCH,
        torznab.MUSIC_SEARCH,
        torznab.BOOK_SEARCH,
        torznab.DETAILS,
        torznab.GETNFO,
        torznab.GET,
        torznab.CART_ADD,
        torznab.CART_DEL,
        torznab.COMMENTS,
        torznab.COMMENTS_ADD,
        torznab.USER,
        torznab.NZB_ADD,
    ):
        return Response(torznab.error(203, "Function not available"))
    else:
        return Response(torznab.error(202, "No such function"))


db.create_all()
app.run(host="0.0.0.0", port=7979)
