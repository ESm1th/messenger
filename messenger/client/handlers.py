import socket
import json
import sys
import os
import logging
import threading
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict

import settings


lock = threading.Lock()
logger = logging.getLogger('client_logger')


class Notifier(ABC):
    """Notifier interface"""

    _state: bool = False

    @abstractmethod
    def add_listener(self, listener: 'Listener', *args, **kwargs) -> None:
        """Adds listener to notifier"""
        pass

    @abstractmethod
    def remove_listener(self, listener: 'Listener') -> None:
        """Remove listener from notifier"""
        pass

    @abstractmethod
    def notify(self, *args, **kwargs) -> None:
        """Notify every listener about changed state"""
        pass


class EndPointNotifier(Notifier):

    _listeners: Dict = {}

    def add_listener(self, event: str, listener: 'Listener') -> None:
        """Adds listener to notifier"""

        if event in self._listeners:
            self._listeners[event].append(listener)
        self._listeners[event] = [listener]

    def remove_listener(self, event: str, listener: 'Listener') -> None:
        """Remove listener from notifier"""

        if len(self._listeners[event]) > 1:
            self._listeners[event].remove(listener)
        else:
            self._listeners.pop(event)

    def notify(self, event: str, *args, **kwargs) -> None:
        """Notify every listener about changed state"""

        for listener in self._listeners[event]:
            listener.refresh(self, *args, **kwargs)


class Listener(ABC):
    """Listener interface"""

    @abstractmethod
    def refresh(self, notifier: Notifier = None, *args, **kwargs) -> None:
        pass


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


class SetupEndPoint(Singleton):

    _default = settings.DEFAULT_SETTINGS

    def __init__(self, endpoint: 'EndPoint'):
        if self._default:
            self.parse_default_settings(endpoint)
        else:
            self.parse_user_settings(endpoint)

    def parse_default_settings(self, endpoint: 'EndPoint'):
        endpoint.ip = getattr(settings, 'HOST', 'localhost')
        endpoint.port = getattr(settings, 'PORT', 7777)
        endpoint.encoding = getattr(settings, 'ENCODING_NAME', 'utf-8')
        endpoint.buffer = getattr(settings, 'BUFFER_SIZE', 1024)

    def parse_user_settings(self, endpoint: 'EndPoint'):
        pass


class RequestCreatorInterface(ABC):
    """Abstract base class for factory method pattern"""

    @abstractmethod
    def create_request(self, data):
        """Create request object"""
        pass


class RequestInterface:
    """Interface for all request objects"""

    action: str = None
    timestamp: float = datetime.now().timestamp()
    data: Dict = {}

    def __init__(self, user_data: Dict = {}) -> None:
        self.data.update(
            {'action': self.action, 'time': self.timestamp, 'data': user_data}
        )

    def prepare(self):
        raw_data = json.dumps(self.data).encode(EndPoint().encoding)
        return raw_data


class RegisterRequest(RequestInterface):
    """Request prepares user data for registration to send over network"""

    action = 'register'


class LoginRequest(RequestInterface):
    """Request prepares user credentials for logginning to send over network"""

    action = 'login'


class EndPointMetaClassResolver(type(Notifier), type(Singleton)):
    """Resolve metaclass conflict when creating 'EndPoint' class (next...)"""
    pass


class EndPoint(
    EndPointNotifier,
    Singleton,
    metaclass=EndPointMetaClassResolver
):

    def __init__(self):
        self._ip = None
        self._port = None
        self._buffer = None
        self._encoding = None
        self.connection = None

    @property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, host):
        self._ip = host
        self.notify('settings')

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, number):
        self._port = number
        self.notify('settings')

    @property
    def buffer(self):
        return self._buffer

    @buffer.setter
    def buffer(self, buffer):
        self._buffer = buffer

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

    def setup(self):
        SetupEndPoint(self)

    def get_address(self):
        return self._ip, self._port

    def make_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.socket = self.make_socket()
            self.socket.connect(self.get_address())
            logger.info('Connection with server established')

            self._state = True
            self.notify('settings')

            response_thread = threading.Thread(
                target=self.get_response, daemon=True
            )
            response_thread.start()

        except Exception as error:
            logger.error(error, exc_info=True)
            print('Connection failed')

    def get_response(self):
        while True:
            raw_response = self.socket.recv(self.buffer)
            response = json.loads(json.loads(raw_response.decode(self.encoding)))
            self.notify('response', **response)

    def send_request(self, request):
        if self._state:
            try:
                self.socket.send(request)
            except Exception as error:
                logger.error(error, exc_info=True)
                raise error
