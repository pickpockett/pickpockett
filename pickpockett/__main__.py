import logging

from . import app

logging.basicConfig(level=logging.INFO)

app.run(host="0.0.0.0", port=9119)
