# import socket
import argparse
import sys
import os
# import json
import logging
import logging.config
import yaml
from PyQt5.QtWidgets import QApplication
import settings

# from protocol import make_request
from core import (
    Client
)
from gui import ClientGui


# getting values from constants in 'settings' module
address = getattr(settings, 'ADDRESS', '')
port = getattr(settings, 'PORT', '7777')
buffer = getattr(settings, 'BUFFER_SIZE', 1024)
encoding_name = getattr(settings, 'ENCODING_NAME', 'utf-8')


# adding arguments to command line and parsing them
parser = argparse.ArgumentParser()
parser.add_argument(
    '-a', '--address', type=str,
    help='Server\'s IP-address'
)
parser.add_argument(
    '-p', '--port', type=int,
    help='Server\'s TCP port'
)
parser.add_argument(
    '-m', '--mode', type=str,
    help='Type of client mode: read - receive responses, write - send requests' 
)
args = parser.parse_args()


# redefining variables 'address' and 'port' if they were
# given as command line arguments
if args.address and args.port:
    address, port = args.address, args.port
elif args.address and not args.port:
    address = args.address
elif args.port and not args.address:
    port = args.port


# load logging config from yaml file and get logger
path = os.path.join(settings.BASE_DIR, 'conflog.yaml')

with open(path, 'r') as file:
    config = yaml.load(file.read(), Loader=yaml.Loader)
    logging.config.dictConfig(config)

logger = logging.getLogger('client_logger')


try:
    app = QApplication([])
    widget = ClientGui()
    sys.exit(app.exec_())
except KeyboardInterrupt:
    logger.info('Client closed')