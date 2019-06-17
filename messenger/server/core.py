import socket
import json
import re
from dis import code_info
from logging import getLogger
from typing import Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime
from argparse import Namespace
from importlib import import_module
from functools import reduce
from select import select

import settings
from db import Base, Session
from observers import (
    BaseNotifier
)


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


class Response:
    """Base response class"""

    time: str = datetime.now().timestamp()
    code: int = 200
    info: str = 'Ok'
    data: Dict[str, Any] = {}

    def __init__(self, request: Request, data: Dict = {}) -> None:

        if bool(self.data):
            self.data.clear()

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


class Settings(Singleton):
    """Server settings"""

    host: str = 'localhost'
    port: PortDescriptor = PortDescriptor()
    buffer_size: int = 1024
    encoding_name: str = 'utf-8'
    connections: int = 5

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

    state: str = 'Disconnected'

    def __init__(self, namespace: Namespace = None):
        self.settings = Settings()
        self.router = Router()
        self.session = Session
        self.notifier = BaseNotifier(self)

    def make_socket(self):

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.settings.host, self.settings.port))
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(0)
            self.socket.listen(self.settings.connections)
            self.state = 'Connected'

            info = 'Server started with {0}:{1}'.format(
                self.settings.host, self.settings.port
            )
            self.notifier.notify('log', info=info)

            return self.socket

        except OSError as error:
            logger.error(error, exc_info=True)
            del self.socket
            self.state = 'Disconnected'
            self.notifier.notify('log', info=str(error))

        finally:
            self.notifier.notify('state')

    def accept_connection(self):
        """Accept connection and return connected socket"""

        client_socket, client_address = self.socket.accept()
        client_socket.setblocking(0)

        info = 'Client with address {} detected'.format(client_address)
        logger.info(info)
        self.notifier.notify('client', info=info)

        return client_socket

    def receive_request(self, client_socket):
        """
        Receiving data from connected socket and return processed request.
        If no data received (client has disconnected) or client connection
        has reset - return None
        """

        try:
            raw_request = client_socket.recv(self.settings.buffer_size)
            request_as_string = raw_request.decode(self.settings.encoding_name)

            logger.info('Request: {0}'.format(request_as_string))

            # self.notifier.notify('log', info=request_as_string)
            self.notifier.notify(
                'request',
                request=json.dumps(json.loads(request_as_string), indent=4)
            )
            print(client_socket.getpeername())

            if raw_request:
                request_attributes = json.loads(
                    raw_request.decode(self.settings.encoding_name)
                )
                print(request_attributes)
                if request_attributes.get('action') == 'login':
                    print(request_attributes)
                    request_attributes['data'].update(
                        {'address': client_socket.getpeername()}
                    )

                request = Request(**request_attributes)
                print(request.data)
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
        logger.info(response.prepare())

        self.notifier.notify(
            'response',
            response=json.dumps(response.data, indent=4)
        )

        return client_socket.send(
            json.dumps(response.prepare()).encode(self.settings.encoding_name)
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

    def close(self):
        if hasattr(self, 'socket'):
            self.state = 'Disconnected'
            self.connections.remove(self.socket)
            self.socket.close()

            self.notifier.notify('state')
            self.notifier.notify('log', info='Server closed')
            logger.info('Server closed')

    def __call__(self):
        """
        Monitor all connected clients with 'select' function.
        'ready_to_read' - list of sockets that have data to read,
        'ready_to_write' - list of sockets that have free buffer and
        able to send data to them.
        """

        self.connections = []
        responses = {}

        server_socket = self.make_socket()
        self.connections.append(server_socket)

        while self.state == 'Connected':
            ready_to_read, ready_to_write, _ = select(
                self.connections, self.connections, self.connections, 0)

            for sock in ready_to_read:
                
                if sock is server_socket:
                    client_socket = self.accept_connection()
                    self.connections.append(client_socket)
                else:
                    request = self.receive_request(sock)

                    if request:
                        response = self.process_request(request)
                        responses[sock.getpeername()] = response
                    else:
                        self.connections.remove(sock)
            if responses:

                for client in responses:

                    for sock in ready_to_write:

                        try:
                            if sock.getpeername() == client:
                                self.send_response(
                                    sock, responses.get(client)
                                )
                        except ConnectionResetError as error:
                            logger.error(error, exc_info=True)
                        except ConnectionAbortedError as error:
                            logger.error(error, exc_info=True)

                responses.clear()
