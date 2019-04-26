import socket
import json
import sys
import os
import logging
import threading
from protocol import make_request


logger = logging.getLogger('client_logger')

lock = threading.Lock()


def make_connection(address, port):
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        connection.connect((address, port))
        logger.info('Connection with server established')
    except Exception as error:
        logger.error(error, exc_info=True)
        print('Connection failed')

    return connection


def send_request(connection, encoding):
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
    while True:
        response = connection.recv(buffer).decode(encoding)
        print('\n{}'.format(json.loads(response).get('data')))


def main_loop(address, port, encoding, buffer):  
    conn = make_connection(address, port)

    response_thread = threading.Thread(
        target=get_response,
        args=(conn, buffer, encoding)
    )
    request_thread = threading.Thread(
        target=send_request,
        args=(conn, encoding)
    )

    response_thread.start()
    request_thread.start()