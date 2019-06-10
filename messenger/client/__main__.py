import argparse
import faulthandler
import sys
import os
import logging
import logging.config

import yaml
from PyQt5.QtWidgets import QApplication

import settings
from gui import ClientGui


faulthandler.enable()


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


# logger configuration
if 'log' not in os.listdir(settings.BASE_DIR):
    os.mkdir(
        ''.join([settings.BASE_DIR, '/log/'])
    )

formatter = logging.Formatter(
    fmt=r'%(asctime)s - %(levelname)s - %(message)s',
    datefmt=r'%Y-%m-%d - %H:%M:%S'
)

handler = logging.FileHandler(
    filename=''.join([settings.BASE_DIR, '/log/client_log.log']),
)

handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)

logger = logging.getLogger('client_logger')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


try:
    app = QApplication([])
    widget = ClientGui()
    sys.exit(app.exec_())
except KeyboardInterrupt:
    logger.info('Client closed')
