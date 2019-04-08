import socket
import argparse
import settings
import handlers


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


try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((address, port))
    sock.listen(5)
    while True:
        print(
            'Server starts with adress {0} and port {1}'.format(address, port)
        )
        client_sock, client_addr = sock.accept()
        print(f'Client with IP address { client_addr } detected')
        data = client_sock.recv(buffer)
        response = handlers.presence_parser(data.decode(encoding_name))
        client_sock.send(response.encode('utf-8'))
        client_sock.close()
except KeyboardInterrupt:
    print('Server closed')
