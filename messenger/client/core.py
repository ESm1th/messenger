import socket
import json
import logging
import threading
from typing import Dict
from argparse import Namespace
from dis import code_info

import settings
from observers import ClientNotifier


logger = logging.getLogger('client_logger')


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


class Setup(Singleton):
    """Setup endpoint settings"""

    _settings: Dict = {}

    def __init__(self, obj) -> None:
        self.target = obj
        self._settings = self.set_settings()

    def set_settings(self) -> None:
        """
        Getting settings values from main settings file - 'settings.py'
        and updates them if arguments were added to command line
        """

        settings_vars = {
            'host': getattr(settings, 'HOST', 'localhost'),
            'port': getattr(settings, 'PORT', 8887),
            'buffer_size': getattr(settings, 'BUFFER_SIZE', 1024),
            'encoding_name': getattr(settings, 'ENCODING_NAME', 'utf-8'),
        }

        return settings_vars

    def update(self, attributes: Dict) -> None:
        """Updates settings dict by passed attributes dict"""

        self._settings.update(
            {
                arg: value
                for arg, value in attributes.items() if value is not None
            }
        )

    def setup(self) -> None:
        """Sets settings to enpoint. Updates existing endpoint attributes."""

        for attribute, value in self._settings.items():
            if hasattr(self.target, attribute):
                setattr(self.target, attribute, value)


class Client(metaclass=ClientVerifier):

    state: bool = False
    host: str = None
    port: int = None
    buffer_size: int = None
    encoding_name: str = None

    # undo comment for testing metaclass realisation
    # socket = socket.socket()

    def __init__(self, namespace: Namespace = None):
        self.notifier = ClientNotifier(self)
        self.setter = Setup(self)

        if namespace is not None:
            if type(namespace) is not Namespace:
                raise TypeError('Argument must be of type "Namespace" class.')

            attributes = dict(namespace._get_kwargs())
            self.setter.update(attributes)
            self.setter.setup()

            super().__init__()
        else:
            raise AttributeError(
                ' '.join(
                    ['Argument must be provided or should not be',
                        'object of NoneType class.']
                )
            )

    def make_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # undo comment for testing metaclass realisation and comment above row
        # return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def connect(self):
        try:
            self.socket = self.make_socket()
            self.socket.connect((self.host, self.port))
            logger.info('Connection with server established')

            self.state = True
            self.notifier.notify('settings')

            response_thread = threading.Thread(
                target=self.get_response, daemon=True
            )
            response_thread.start()

        except Exception as error:
            logger.error(error, exc_info=True)
            print('Connection failed')

    def get_response(self):
        while True:
            raw_response = self.socket.recv(self.buffer_size)
            response = json.loads(
                json.loads(raw_response.decode(self.encoding_name))
            )
            self.notifier.notify('response', **response)

    def send_request(self, request):
        if self.state:
            try:
                self.socket.send(request)
            except Exception as error:
                logger.error(error, exc_info=True)
                raise error
