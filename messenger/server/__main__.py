import os
import sys
import logging
import logging.config
import argparse
import faulthandler

from PyQt5.QtWidgets import QApplication

import settings
from core import Server
from gui import ServerGui


faulthandler.enable()


# adding arguments to command line and parsing them
parser = argparse.ArgumentParser()
parser.add_argument(
    '-a', '--address', type=str,
    help='IP-address using for socket binding'
)
parser.add_argument(
    '-p', '--port', type=int,
    help='TCP port using for socket binding'
)
parser.add_argument(
    '-g', '--gui', action='store_const', const=True, default=False
)
args = parser.parse_args()


# logger configuration
if 'log' not in os.listdir(settings.BASE_DIR):
    os.mkdir(
        ''.join([settings.BASE_DIR, '/log/'])
    )

formatter = logging.Formatter(
    fmt=r'%(asctime)s - %(levelname)s - %(message)s',
    datefmt=r'%Y-%m-%d - %H:%M:%S'
)

handler = logging.handlers.TimedRotatingFileHandler(
    filename=''.join([settings.BASE_DIR, '/log/server_log.log']),
    when='D',
    interval=1,
)

handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)

logger = logging.getLogger('server_logger')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


try:
    if args.gui:
        app = QApplication([])
        widget = ServerGui()
        sys.exit(app.exec_())
    else:
        server = Server()
        if args.address and args.port:
            cmd_settings = {
                'host': args.address,
                'port': args.port
            }
            server.settings.update(cmd_settings)
        server.run()
except KeyboardInterrupt:
    logger.info('Server closed')
