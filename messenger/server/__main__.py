import argparse
import json
import yaml
import os
import logging
import logging.config

import settings
from handlers import (
    make_server_socket, accept_connection,
    receive_request, process_request,
    send_response, main_loop
)


# getting values from constants in 'settings' module
address = getattr(settings, 'ADDRESS', '')
port = getattr(settings, 'PORT', '7777')


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
path = os.path.join(os.path.dirname(__file__), 'conflog.yaml')

with open(path, 'r') as file:
    config = yaml.load(file.read(), Loader=yaml.Loader)
    logging.config.dictConfig(config)

logger = logging.getLogger('server_logger')


try:
    main_loop(address, port)
except KeyboardInterrupt:
    logger.info('Server closed')
