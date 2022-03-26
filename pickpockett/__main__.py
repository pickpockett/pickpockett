import logging
import socket

import waitress
from paste.translogger import TransLogger
from werkzeug.serving import get_interface_ip

from . import App

logging.basicConfig(level=logging.INFO)

hostname = get_interface_ip(socket.AF_INET)
waitress.serve(TransLogger(App()), host=hostname, port=9119)
