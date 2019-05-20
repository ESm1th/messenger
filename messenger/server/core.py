from __future__ import annotations
import socket
import json
import re
from dis import code_info
from logging import getLogger
from typing import Dict
from abc import ABC, abstractmethod
from datetime import datetime
from argparse import Namespace
from importlib import import_module
from functools import reduce
from select import select

import settings
from db import Base, Session


logger = getLogger('server_logger')


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


class Request:
    """Represents received data from client socket."""

    action: str = None
    data: Dict = {}

    def __init__(self, **kwargs):
        [
            setattr(self, attr, value) for attr, value in kwargs.items()
            if hasattr(self, attr)
        ]

    def is_valid(self):
        if not self.action:
            return False
        return True


class RequestHandler(ABC):
    """
    Interface for all request handlers classes.
    'Controller' design pattern.
    """

    model: Base = None

    def __init__(self, request: Request, session: Session) -> None:
        self.request = request
        self.session = session

        logger.info(f'Controller: "{self}" was called.')

    @abstractmethod
    def process(self) -> Response:
        pass

    @abstractmethod
    def validate_request(self, data) -> bool:
        pass


class Response:
    """Base response class"""

    time: str = datetime.now().timestamp()
    code: int = 200
    info: str = 'Ok'
    data: Dict = {}

    def __init__(self, request: Request, data: Dict = {}) -> None:
        self.data.update(
            {
                'action': request.action,
                'timestamp': self.time,
                'code': self.code,
                'info': self.info,
            }
        )
        self.data.update(**data)

    def prepare(self):
        return json.dumps(self.data)


class Response_400(Response):

    code = 400
    info = 'Wrong request format'


class Response_404(Response):

    code = 404
    info = 'Action is not supported'


class Response_403(Response):

    code = 403
    info = 'Access denied'


class Response_500(Response):

    code = 500
    info = 'Internal server error'


class Router(Singleton):
    """
    Maintains server routes and resolves requests from client
    (gets action from request and return appropriate controller)
    """

    def server_routes(self):
        """
        Return list of all routes from each module
        in INSTALLED_MODULES - [ {action: controller}, ... ]
        """

        return reduce(
            lambda routes, module: routes + getattr(
                import_module(f'{ module }.routes'), 'routes', []
            ),
            settings.INSTALLED_MODULES,
            []
        )

    def routes_map(self):
        """
        Return dict with actions as keys and controllers as values
        from 'self.routes'
        """

        return {
            route['action']: route['controller']
            for route in self.server_routes()
        }

    def actions(self):
        """
        Return list of all possible actions from 'self.routes'
        """
        return [
            *self.routes_map().keys()
        ]

    def validate_action(self, action):
        """
        Returns 'True' if passed 'action' exists in all possible routes
        or returns 'False' otherwise
        """

        if action in self.actions():
            return True

    def resolve(self, action):
        """
        Return controller for passed action if action
        exists in all server routes.
        Return None if passed action not exists in routes.
        """

        return self.routes_map().get(action, None)


class Setup(Singleton):
    """Setup endpoint settings"""

    _settings: Dict = {}

    def __init__(self, obj) -> None:
        self.target = obj
        self._settings = self.set_settings()

    def set_settings(self) -> Dict:
        """
        Getting settings values from main settings file - 'settings.py'
        and updates them if arguments were added to command line
        """

        settings_vars = {
            'host': getattr(settings, 'HOST', 'localhost'),
            'port': int(getattr(settings, 'PORT', 8887)),
            'buffer_size': getattr(settings, 'BUFFER_SIZE', 1024),
            'encoding_name': getattr(settings, 'ENCODING_NAME', 'utf-8'),
            'connections': getattr(settings, 'CONNECTIONS', 5)
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


class PortDescriptor:
    """
    Descriptor class for servers port attribute.
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


class ServerVerifier(type):
    """Metaclass for checking server class creation"""

    _instance = None

    def __call__(self, *args, **kwargs):
        if not self._instance:
            self._instance = super().__call__(*args, **kwargs)
        return self._instance

    def __init__(self, cls, bases, cls_dict):

        for attr, value in cls_dict.items():
            if hasattr(value, '__call__'):
                code_data = code_info(value)
                pattern = r'\bconnect\b'

                if re.search(pattern, code_data):
                    raise AttributeError(
                        ' '.join(
                            ['Server socket must not have',
                                '"connect"',
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

        type.__init__(self, cls, bases, cls_dict)


class Server(metaclass=ServerVerifier):

    # state: bool = False
    host: str = None
    port: PortDescriptor = PortDescriptor()
    buffer_size: int = None
    encoding_name: str = None
    connections: int = None

    def __init__(self, namespace: Namespace = None):
        self.router = Router()
        self.session = Session
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

    # undo comment for testing metaclass realisation
    # def connect(self):
    #     self.connect()

    def make_socket(self):
        # undo comment for testing metaclass realisation and comment below row
        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(0)
        self.socket.listen(self.connections)
        return self.socket

    def accept_connection(self):
        """Accept connection and return connected socket"""

        client_socket, client_address = self.socket.accept()
        client_socket.setblocking(0)

        logger.info(
            'Client with address {} detected'.format(client_address)
        )
        print('Client with address {} detected'.format(client_address))

        return client_socket

    def receive_request(self, client_socket):
        """
        Receiving data from connected socket and return processed request.
        If no data received (client has disconnected) or client connection
        has reset - return None
        """

        try:
            raw_request = client_socket.recv(self.buffer_size)

            if raw_request:
                request_attributes = json.loads(
                    raw_request.decode(self.encoding_name)
                )
                request = Request(**request_attributes)
                return request
            else:
                logger.info(
                    'Client {} disconnected'.format(
                        client_socket.getpeername()
                    )
                )
                client_socket.close()

        except ConnectionResetError as error:
            logger.error(error, exc_info=True)
        except ConnectionAbortedError as error:
            logger.error(error, exc_info=True)

    def send_response(self, client_socket, response):
        """Send response to client"""

        logger.info(f'Response {response} sent.')
        return client_socket.send(
            json.dumps(response.prepare()).encode(self.encoding_name)
        )

    def process_request(self, request):
        """Processing received request from client"""

        if request.is_valid():
            action = request.action

            if self.router.validate_action(action):
                controller = self.router.resolve(action)

                if controller:
                    try:
                        return controller(request, self.session).process()
                    except Exception:
                        logger.critical('Exception occurred', exc_info=True)
                        return Response_500(request)
            else:
                logger.error(
                    'Action {} does not exists'.format(request.action)
                )
                return Response_404(request)
        else:
            logger.error('Request is not valid')
            return Response_400(request)

    def __call__(self):
        """
        Monitor all connected clients with 'select' function.
        'ready_to_read' - list of sockets that have data to read,
        'ready_to_write' - list of sockets that have free buffer and
        able to send data to them.
        """

        connections = []
        responses = {}

        server_socket = self.make_socket()
        connections.append(server_socket)

        while True:
            ready_to_read, ready_to_write, _ = select(
                connections, connections, connections, 0)

            for sock in ready_to_read:

                if sock is server_socket:
                    client_socket = self.accept_connection()
                    connections.append(client_socket)
                else:
                    request = self.receive_request(sock)

                    if request:
                        response = self.process_request(request)
                        responses.update({sock.getpeername(): response})
                    else:
                        connections.remove(sock)
            if responses:

                for client in responses:

                    for sock in ready_to_write:

                        try:
                            # if sock.getpeername() != client:
                            self.send_response(
                                sock, responses.get(client)
                            )
                        except ConnectionResetError as error:
                            logger.error(error, exc_info=True)
                        except ConnectionAbortedError as error:
                            logger.error(error, exc_info=True)

                responses.clear()
