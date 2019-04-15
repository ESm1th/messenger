import socket
import argparse
import json
import yaml
import os
import logging
import logging.config
import settings
from protocol import (
    validate_request, make_response,
    make_400, make_404,
    validate_action
)
from routes import resolve


# getting values from constants in 'settings' module
address = getattr(settings, 'ADDRESS', '')
port = getattr(settings, 'PORT', '7777')
buffer = getattr(settings, 'BUFFER_SIZE', 1024)
encoding_name = getattr(settings, 'ENCODING_NAME', 'utf-8')


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
    config = yaml.load(file.read())
    logging.config.dictConfig(config)

logger = logging.getLogger('server_logger')


try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((address, port))
    sock.listen(5)

    logger.info(
        'Server started with adress {0} and port {1}'.format(
            address or 'localhost', port
        )
    )

    while True:
        client_sock, client_addr = sock.accept()
        logger.info(f'Client with address { client_addr } detected')

        data = client_sock.recv(buffer)
        request = json.loads(
            data.decode(encoding_name)
        )
        action_name = request.get('action')

        if validate_request(request):
            if validate_action(request):
                controller = resolve(action_name)
                if controller:
                    try:
                        response = controller(request)

                        if response.get('code') != 200:
                            message = response.get('data')
                            logger.error(f'{ message }')
                        else:
                            logger.info(
                                f'Function { controller.__name__ } was called'
                            )
                    except Exception:
                        logger.critical('Exception occurred', exc_info=True)
                        response = make_response(
                            request, 500, 'Internal server error'
                        )
            else:
                logger.error(f'Action { action_name } does not exists')
                response = make_404(request)
        else:
            logger.error('Request is not valid')
            response = make_400(request)

        client_sock.send(
            json.dumps(response).encode(encoding_name)
        )
except KeyboardInterrupt:
    logger.info('Server closed')
