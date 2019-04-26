# import socket
import argparse
# import json
import logging
import logging.config
import yaml
import settings
import os
# from protocol import make_request
from handlers import (
    make_connection,
    send_request,
    get_response,
    main_loop
)


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
path = os.path.join(os.path.dirname(__file__), 'conflog.yaml')

with open(path, 'r') as file:
    config = yaml.load(file.read())
    logging.config.dictConfig(config)

logger = logging.getLogger('client_logger')


try:
    main_loop(address, port, encoding_name, buffer)
except KeyboardInterrupt:
    logger.info('Client closed')
