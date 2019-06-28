import socket
import json
import logging
import ftplib
from io import BytesIO
from typing import Dict
from argparse import Namespace
from dis import code_info

import settings
from observers import (
    BaseNotifier,
    StatusListener
)


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


class Status(Singleton):

    def __init__(self, notifier):
        self.listener = StatusListener(self, notifier)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in ('code', 'info'):
                setattr(self, key, str(value))


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


class FtpClient(Singleton):
    """Represent ftp client"""

    ftp_settings = (
        'ftp_host',
        'ftp_user',
        'ftp_password',
        'ftp_path'
    )

    def __init__(self) -> None:
        for attr in self.ftp_settings:
            val = getattr(settings, attr.upper(), None)
            setattr(self, attr, val)

    def connect(self):
        self.connection = ftplib.FTP(
            host=self.ftp_host,
            user=self.ftp_user,
            passwd=self.ftp_password,
        )

    def upload_file(self, filename, bytes_data):
        try:
            self.connection.cwd(self.ftp_path)
            status = self.connection.storbinary(
                ' '.join(['STOR', filename]), bytes_data
            )

            if not status.startswith('226 Transfer complete'):
                return False
            return True

        finally:
            self.connection.quit()

    def download_file(self, filename):
        try:
            self.connection.cwd(self.ftp_path)

            in_memory_file = BytesIO()

            status = self.connection.retrbinary(
                ' '.join(['RETR', filename]), in_memory_file.write
            )

            if not status.startswith('226 Transfer complete'):
                return False
            return in_memory_file

        finally:
            self.connection.quit()


class Client(metaclass=ClientVerifier):

    state = False

    def __init__(self, namespace: Namespace = None):
        self.notifier = BaseNotifier(self)
        self.status = Status(self.notifier)
        self.settings = Settings()

    def make_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock

    def connect(self):
        try:
            self.socket = self.make_socket()
            self.socket.connect((self.settings.host, self.settings.port))
            logger.info('Connection with server established')

            self.state = True
            self.notifier.notify('state')
            self.get_response()

        except Exception as error:
            self.state = False
            self.notifier.notify('state')
            logger.error(error, exc_info=True)
            print('Connection failed')

    def get_response(self):

        while self.state:
            try:
                raw_response = self.socket.recv(self.settings.buffer_size)
                if raw_response:
                    response = json.loads(
                        json.loads(
                            raw_response.decode(self.settings.encoding_name)
                        )
                    )
                    # print('response: ', response)
                    self.notifier.notify('response', **response)
            except Exception as error:
                self.state = False
                self.notifier.notify('state')
                raise error

    def send_request(self, request):

        if self.state:
            try:
                self.socket.send(request)
            except Exception as error:
                logger.error(error, exc_info=True)
                raise error

    def close(self):
        if self.socket:
            self.socket.shutdown(socket.SHUT_RD)
            # self.socket.close()
