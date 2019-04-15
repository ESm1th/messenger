import socket
import argparse
import json
import logging
import logging.config
import yaml
import settings
import os
from protocol import make_request


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
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((address, port))
        logger.info('Connection with server established')
    except Exception as error:
        logger.error('Connection failed', exc_info=True)
        raise error

    action = input('Please enter action name: ')
    data = input('Please enter data: ')
    logger.info(f'Entered action: { action }, entered data: { data }')

    request = make_request(action, data=data)

    try:
        sock.send(json.dumps(request).encode(encoding_name))
    except Exception as error:
        logger.error('Error occurred', exc_info=True)
        raise error

    response = sock.recv(buffer).decode(encoding_name)
    print(json.loads(response).get('data'))
    sock.close()
    logger.info('Client closed')
except KeyboardInterrupt:
    logger.info('Client closed')
