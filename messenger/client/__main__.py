import socket
import argparse
import settings
import handlers
import os

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


try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address, port))
    message = handlers.presence_message(username=os.getlogin())
    sock.send(message.encode(encoding_name))
    data = sock.recv(buffer)
    handlers.presence_response_parser(data.decode(encoding_name))
    sock.close()
except KeyboardInterrupt:
    print('Client closed')
