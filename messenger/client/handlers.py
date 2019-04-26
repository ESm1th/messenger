import socket
import json
import sys
import os
import logging
import threading
from protocol import make_request


logger = logging.getLogger('client_logger')


def make_connection(address, port):
    """Make socket and connect to server"""

    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        connection.connect((address, port))
        logger.info('Connection with server established')
    except Exception as error:
        logger.error(error, exc_info=True)
        print('Connection failed')

    return connection


def send_request(connection, encoding):
    """Get data from user, make request object and send it to server"""

    while True:
        action = input('Please enter action name: ')
        data = input('Please enter data: ')

        request = make_request(action=action, data=data, user=os.getlogin())

        try:
            connection.send(json.dumps(request).encode(encoding))
        except Exception as error:
            logger.error(error, exc_info=True)
            print('Error occurred')


def get_response(connection, buffer, encoding):
    """Receive data from server and print it to console"""

    while True:
        response = connection.recv(buffer).decode(encoding)
        print('\n{}'.format(json.loads(response).get('data')))


def main_loop(address, port, encoding, buffer):
    """
    Make connection and starting two threads:
    - one for input data and send request
    - one for receive response
    """

    conn = make_connection(address, port)

    response_thread = threading.Thread(
        target=get_response, args=(conn, buffer, encoding)
    )

    request_thread = threading.Thread(
        target=send_request, args=(conn, encoding)
    )

    response_thread.start()
    request_thread.start()
