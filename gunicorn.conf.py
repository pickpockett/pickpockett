import socket

from werkzeug.serving import get_interface_ip

if (ip := get_interface_ip(socket.AF_INET)) == "127.0.0.1":
    ip = "0.0.0.0"

accesslog = "-"
bind = f"{ip}:9119"
