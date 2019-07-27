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
import asyncio

import settings
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

    action = None
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

    time = datetime.now().timestamp()
    code = 200
    info = 'Ok'
    data = {}

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

    model = None

    def __init__(self, request: Request) -> None:
        self.request = request
        logger.info('Controller: "{}" was called.'.format(self))

    @abstractmethod
    def process(self) -> Response:
        pass

    def validate_request(self) -> bool:
        """
        Checks if username is not None
        and if it is not empty string
        """
        return bool(self.request.data.get('username'))


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
                import_module('{}.routes'.format(module)), 'routes', []
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

    host = 'localhost'
    port = PortDescriptor()
    buffer_size = 1024
    encoding_name = 'utf-8'
    connections = 5

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
                            [
                                'Server socket must not have',
                                '"connect"',
                                'calls in code. Check "{}" method'.format(attr)
                            ]
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

    state = 'Disconnected'

    def __init__(self, namespace: Namespace = None):
        self.settings = Settings()
        self.router = Router()
        self.notifier = BaseNotifier(self)

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

        loop.connections = []
        loop.clients = {}

        endpoint_factory = asyncio.start_server(
            self.handle_connection,
            host=self.settings.host,
            port=self.settings.port,
        )

        self.endpoint = loop.run_until_complete(endpoint_factory)
        self.state = 'Connected'

        info = 'Server started with {0}:{1}'.format(
            self.settings.host, self.settings.port
        )
        logger.info(info)
        self.notifier.notify('log', info=info)
        self.notifier.notify('state')

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print('App closed from key')
        except Exception as error:
            logger.error(error, exc_info=True)
            self.state = 'Disconnected'
            self.notifier.notify('log', info=str(error))
        finally:
            self.close()

    async def handle_connection(self, reader, writer):
        """
        Handles connections: reads from reader stream, writes to writer stream.
        """

        address = writer.get_extra_info('peername')
        info = 'Client with address {} detected'.format(address)
        logger.info(info)
        self.notifier.notify('log', info=info)

        loop = asyncio.get_event_loop()
        loop.connections.append(writer)

        while True:
            raw_request = await reader.read(self.settings.buffer_size)

            if raw_request:
                request_as_string = raw_request.decode(
                    self.settings.encoding_name
                )

                logger.info('Request: {0}'.format(request_as_string))

                self.notifier.notify(
                    'request',
                    request=json.dumps(
                        json.loads(request_as_string),
                        indent=4
                    )
                )

                request_attributes = json.loads(
                    raw_request.decode(self.settings.encoding_name)
                )
                request = Request(**request_attributes)

                response = await self.process_request(request)
                if response:
                    if response.data.get('action') != 'logout':

                        if response.data.get('action') == 'login':
                            data = response.data.get('user_data')
                            if data:
                                loop.clients.update(
                                    {data.get('username'): writer}
                                )
                                self.notifier.notify(
                                    'client',
                                    action='add',
                                    data=data.get('username')
                                )

                        prepared_response = json.dumps(
                            response.prepare()
                        ).encode(self.settings.encoding_name)

                        if response.data.get('action') == 'add_message':
                            client = response.data.get('contact_username')

                            if not client:
                                for client in loop.clients:
                                    client_writer = loop.clients[client]

                                    if client_writer is not writer:
                                        client_writer.write(prepared_response)
                                        await client_writer.drain()
                            else:
                                if client in loop.clients:
                                    client_write = loop.clients[client]
                                    client_write.write(
                                        prepared_response
                                    )
                                    await client_write.drain()

                        writer.write(prepared_response)
                        await writer.drain()
                    else:
                        user = response.data.get('username')
                        loop.clients.pop(user)
                        self.notifier.notify(
                            'client',
                            action='delete',
                            data=user
                        )

                logger.info('Response {} sent.'.format(response))
                logger.info(prepared_response)

                self.notifier.notify(
                    'response',
                    response=json.dumps(
                        response.data, indent=4
                    )
                )
            else:
                writer.close()
                logger.info('Client {} disconnected'.format(address))
                return

    async def process_request(self, request):
        """Processing received request from client"""

        if request.is_valid():
            action = request.action

            if self.router.validate_action(action):
                controller = self.router.resolve(action)

                if controller:
                    try:
                        return controller(request).process()
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
        if hasattr(self, 'endpoint'):
            loop = asyncio.get_event_loop()
            self.endpoint.close()

            loop.run_until_complete(self.endpoint.wait_closed())
            del self.endpoint

            self.state = 'Disconnected'
            self.notifier.notify('state')
