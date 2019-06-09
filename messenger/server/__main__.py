import os
import sys
import logging
import logging.config
import argparse
import faulthandler

import yaml
from PyQt5.QtWidgets import QApplication

from gui import ServerGui


faulthandler.enable()


# adding arguments to command line and parsing them
parser = argparse.ArgumentParser()
parser.add_argument(
    '-a', '--host', type=str,
    help='IP-address using for socket binding'
)
parser.add_argument(
    '-p', '--port', type=int,
    help='TCP port using for socket binding'
)
args = parser.parse_args()


# load logging config from yaml file and get logger
path = os.path.join(os.path.dirname(__file__), 'conflog.yaml')

with open(path, 'r') as file:
    config = yaml.load(file.read(), Loader=yaml.Loader)
    logging.config.dictConfig(config)

logger = logging.getLogger('server_logger')


try:
    app = QApplication([])
    widget = ServerGui()
    sys.exit(app.exec_())
except KeyboardInterrupt:
    logger.info('Server closed')
