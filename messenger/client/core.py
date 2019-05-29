import socket
import json
import logging
import threading
from typing import Dict
from argparse import Namespace
from dis import code_info

import settings
from observers import BaseNotifier


logger = logging.getLogger('client_logger')
lock = threading.Lock()

class SingletonMeta(type):
    """Singleton realisation with metaclass"""

    _instance = None

    def __call__(self, *args, **kwargs):
        if not self._instance:
            self._instance = super().__call__(*args, **kwargs)
        return self._instance


class Singleton(metaclass=SingletonMeta):
    """Base singleton class"""
    pass


class ClientVerifier(type):

    _instance = None

    def __call__(self, *args, **kwargs):
        if not self._instance:
            self._instance = super().__call__(*args, **kwargs)
        return self._instance

    def __init__(self, cls, bases, cls_dict):
        for attr, value in cls_dict.items():

            if hasattr(value, '__call__'):
                code_data = code_info(value)

                for element in ['accept', 'listen']:
                    if element in code_data:
                        raise AttributeError(
                            ' '.join(
                                ['Client socket must not have',
                                    '"accept" and "listen".',
                                    f'calls in code. Check "{attr}" method']
                            )
                        )

                if 'SOCK_' in code_data:
                    if 'SOCK_STREAM' not in code_data:
                        raise AttributeError(
                            ' '.join(
                                ['Only TCP socket type allowed,',
                                    'but other was given']
                            )
                        )

            elif not hasattr(value, '__call__'):
                if type(value) == socket.socket:
                    raise AttributeError(
                        'Not allowed to create a socket at the class level'
                    )

        type.__init__(self, cls, bases, cls_dict)


class PortDescriptor:
    """
    Descriptor class for client port attribute.
    This descriptor adds validation for setting port number.
    """

    def __init__(self):
        self._value = 7777

    def __get__(self, instance, instance_type):
        return self._value

    def __set__(self, instance, value):
        if type(value) is not int:
            raise TypeError('Value must be integer')
        if not value >= 0:
            raise ValueError('Port number must be => 0')
        self._value = value


class Settings(Singleton):
    """Server settings"""

    host: str = 'localhost'
    port: PortDescriptor = PortDescriptor()
    buffer_size: int = 1024
    encoding_name: str = 'utf-8'

    def __init__(self) -> None:
        for attr, value in self.__class__.__dict__.items():
            if not hasattr(value, '__call__'):
                val = getattr(settings, attr.upper(), None)
                if val != value and val is not None:
                    setattr(self, attr, val)

    def update(self, attributes: Dict) -> None:
        """Updates settings attributes by passed attributes dict"""

        for attr, value in attributes.items():
            if hasattr(self, attr):
                setattr(self, attr, value)


class Client(metaclass=ClientVerifier):

    state = 'Disconnected'

    def __init__(self, namespace: Namespace = None):
        self.notifier = BaseNotifier(self)
        self.settings = Settings()

    def set_state(self, state):
        self.state = state

    def make_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock

    def connect(self):
        try:
            self.socket = self.make_socket()
            self.socket.connect((self.settings.host, self.settings.port))
            logger.info('Connection with server established')

            self.state = 'Connected'
            self.notifier.notify('status')
            print('connect')
            response_thread = threading.Thread(
                target=self.get_response
            )
            response_thread.start()

        except Exception as error:
            self.state = 'Disconnected'
            self.notifier.notify('status')
            logger.error(error, exc_info=True)
            print('Connection failed')

    def get_response(self):

        while self.state == 'Connected':
            try:
                raw_response = self.socket.recv(self.settings.buffer_size)
                print('response: {}'.format(raw_response))
                if raw_response:
                    response = json.loads(
                        json.loads(
                            raw_response.decode(self.settings.encoding_name)
                        )
                    )
                    self.notifier.notify('response', **response)
                    print('the end')
            except Exception as error:
                self.state = False
                self.notifier.notify('status')
                print('before error')
                raise error
        

    def send_request(self, request):

        if self.state == 'Connected':
            try:
                print(request)
                self.socket.send(request)
                print('request sent')
            except Exception as error:
                logger.error(error, exc_info=True)
                raise error

    def close(self):
        if self.socket:
            
            print('socket exist')
            print(self.socket.fileno())
            self.socket.shutdown(socket.SHUT_RD)
            # self.socket.close()
            print('shutdown')
        

