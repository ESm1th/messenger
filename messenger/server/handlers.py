import socket
import logging
import json
from select import select

import settings
from protocol import (
    validate_request, validate_action,
    make_400, make_404, make_response
)
from routes import resolve


buffer = getattr(settings, 'BUFFER_SIZE', 1024)
encoding_name = getattr(settings, 'ENCODING_NAME', 'utf-8')


logger = logging.getLogger('server_logger')


def make_server_socket(address, port, connections):
    """Return socket with passed parameters"""

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0)
    sock.bind((address, port))
    sock.listen(connections)
    sock.settimeout(0)

    logger.info(
            'Server started with adress {0} and port {1}'.format(
                address or 'localhost', port
            )
    )

    return sock


def accept_connection(server_socket):
    """Accept connection and return connected socket"""

    client_socket, client_address = server_socket.accept()
    client_socket.setblocking(0)
    
    logger.info(
        'Client with address {} detected'.format(client_address)
    )
    print('Client with address {} detected'.format(client_address))
    
    return client_socket


def receive_request(client_socket):
    """
    Receiving data from connected socket and return processed request.
    If no data received (client has disconnected) or client connection
    has reset - return None
    """
    try:
        raw_request = client_socket.recv(buffer)

        if raw_request:
            request = json.loads(raw_request.decode(encoding_name))
            return request
        else:
            logger.info(
                'Client {} disconnected'.format(client_socket.getpeername())
            )

    except ConnectionResetError as error:
        logger.error(error, exc_info=True)
    except ConnectionAbortedError as error:
        logger.error(error, exc_info=True)


def process_request(request):
    """Processing received request from client"""

    if validate_request(request):
        action = request.get('action')

        if validate_action(action):
            controller = resolve(action)

            if controller:
                try:
                    response = controller(request)

                    if response.get('code') != 200:
                        message = response.get('data')
                        logger.error('{}'.format(message))
                    else:
                        logger.info(
                            'Function {} was called'.format(
                                controller.__name__
                            )
                        )
                except Exception:
                    logger.critical('Exception occurred', exc_info=True)
                    response = make_response(
                        request, 500, 'Internal server error'
                    )
        else:
            logger.error(
                'Action {} does not exists'.format(action)
            )
            response = make_404(request)
    else:
        logger.error('Request is not valid')
        response = make_400(request)   
    
    return response


def send_response(client_socket, response):
    """Send response to client"""

    return client_socket.send(
        json.dumps(response).encode(encoding_name)
    )


def main_loop(address, port):
    """
    Monitor all connected clients with 'select' function.
    
    'ready_to_read' - list of sockets that have data to read,
    'ready_to_write' - list of sockets that have free buffer and
    able to send data to them.

    Data from client in 'write' mode send to every client with 'read' mode.
    """

    connections = []
    responses = []

    server_socket = make_server_socket(address, port, 5)
    connections.append(server_socket)

    while True:
        ready_to_read, ready_to_write, _ = select(
            connections, connections, connections, 0)

        for sock in ready_to_read:

            if sock is server_socket:
                client_socket = accept_connection(sock)
                connections.append(client_socket)
            else:
                request = receive_request(sock)

                if request:
                    response = process_request(request)
                    responses.append(response)
        
        if responses:

            for response in responses:
                response = responses.pop()
            
                for sock in ready_to_write:
                    try:
                        send_response(sock, response)
                    except ConnectionResetError as error:
                        logger.error(error, exc_info=True)
                    except ConnectionAbortedError as error:
                        logger.error(error, exc_info=True)


            
