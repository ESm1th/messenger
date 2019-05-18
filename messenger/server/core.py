from __future__ import annotations
import socket
import json
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
        Return controller for passed action if action exists in passed
        list of routes, if this list is not None, 
        or in all server routes, otherwise.
        Return None if passed action not exists in routes return None.
        """

        return self.routes_map().get(action, None)


class SetUpConnection(Singleton):
    """Setup endpoint settings"""

    _settings: Dict = {}

    def __init__(self, arguments: Namespace) -> None:
        self._args = dict(arguments._get_kwargs())
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
            'connections': getattr(settings, 'CONNECTIONS', 5)
        }

        settings_vars.update(
            {
                arg: value
                for arg, value in self._args.items() if value is not None
            }
        )

        return settings_vars

    def setup(self, endpoint: EndPoint) -> None:
        """Sets settings to enpoint. Updates existing endpoint attributes."""

        for attribute, value in self._settings.items():
            if hasattr(endpoint, attribute):
                setattr(endpoint, attribute, value)


class EndPoint(Singleton):

    _socket: socket.socket = None
    _host: str = None
    _port: int = None
    _buffer_size: int = None
    _encoding_name: str = None
    _connections: int = None

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        self._host = host

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, number):
        self._port = number

    @property
    def buffer_size(self):
        return self._buffer_size

    @buffer_size.setter
    def buffer_size(self, buffer):
        self._buffer_size = buffer

    @property
    def encoding_name(self):
        return self._encoding_name

    @encoding_name.setter
    def encoding_name(self, encoding):
        self._encoding_name = encoding

    @property
    def connections(self):
        return self._connections

    @connections.setter
    def connections(self, value):
        self._connections = value

    def get_address(self):
        return self._host, self._port

    def setup(self, service: SetUpConnection) -> None:
        service.setup(self)

    def make_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(self.get_address())
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.settimeout(0)
        self._socket.listen(self.connections)
        return self._socket

    def accept_connection(self):
        """Accept connection and return connected socket"""

        client_socket, client_address = self._socket.accept()
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


class Server(Singleton):

    _endpoint: EndPoint = None
    _router: Router = None
    _session: Session = None

    @property
    def endpoint(self):
        return self._endpoint

    def set_endpoint(self, endpoint: EndPoint) -> None:
        self._endpoint = endpoint

    @property
    def router(self):
        return self._router

    def set_router(self, router: Router) -> None:
        self._router = router

    @property
    def session(self):
        return self._session

    def set_session(self, session: Session) -> None:
        self._session = session

    def __call__(self):
        """
        Monitor all connected clients with 'select' function.
        'ready_to_read' - list of sockets that have data to read,
        'ready_to_write' - list of sockets that have free buffer and
        able to send data to them.
        """

        connections = []
        responses = {}

        server_socket = self.endpoint.make_socket()
        connections.append(server_socket)

        while True:
            ready_to_read, ready_to_write, _ = select(
                connections, connections, connections, 0)

            for sock in ready_to_read:

                if sock is server_socket:
                    client_socket = self.endpoint.accept_connection()
                    connections.append(client_socket)
                else:
                    request = self.endpoint.receive_request(sock)

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
                            self.endpoint.send_response(
                                sock, responses.get(client)
                            )
                        except ConnectionResetError as error:
                            logger.error(error, exc_info=True)
                        except ConnectionAbortedError as error:
                            logger.error(error, exc_info=True)

                responses.clear()

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
