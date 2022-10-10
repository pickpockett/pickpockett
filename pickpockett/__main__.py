import os
import socket

import waitress
from paste.translogger import TransLogger
from werkzeug.serving import get_interface_ip

from . import app

if os.environ.get("DEBUG") not in (None, "0"):
    hostname = "127.0.0.1"
elif (hostname := get_interface_ip(socket.AF_INET)) == "127.0.0.1":
    hostname = "0.0.0.0"

waitress.serve(TransLogger(app), host=hostname, port=9119)
