import socket
import argparse
import json
import sys
import logging
import string
import settings
from protocol import (
    validate_request, make_response,
    make_400, make_404
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


# define logger object
splitter_symbols = string.punctuation + string.whitespace
logger = logging.getLogger(
    __name__ if __name__ != '__main__' else sys.argv[0].split(splitter_symbols)
)


try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((address, port))
    sock.listen(5)
    print(
        'Server starts with adress {0} and port {1}'.format(address, port)
    )
    while True:
        client_sock, client_addr = sock.accept()
        print(f'Client with IP address { client_addr } detected')
        data = client_sock.recv(buffer)

        request = json.loads(
            data.decode(encoding_name)
        )
        action_name = request.get('action')

        if validate_request(request):
            controller = resolve(action_name)
            if controller:
                try:
                    response = controller(request)
                except Exception as error:
                    print(error)
                    response = make_response(
                        request, 500, 'Internal server error'
                    )
            else:
                print(f'Action { action_name } does not exists')
                response = make_404(request)
        else:
            print('Request is not valid')
            response = make_400(request)

        client_sock.send(
            json.dumps(response).encode(encoding_name)
        )
        client_sock.close()
except KeyboardInterrupt:
    print('Server closed')
