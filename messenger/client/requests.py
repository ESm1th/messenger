from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict
import json

from core import Client


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
        raw_data = json.dumps(self.data)
        return raw_data


class RegistrationRequest(RequestInterface):
    """Request prepares user data for registration to send over network"""

    action = 'register'


class LoginRequest(RequestInterface):
    """Request prepares user credentials for logginning to send over network"""

    action = 'login'


class ChatRequest(RequestInterface):

    action = 'chat'


class RequestCreatorInterface(ABC):
    """Abstract base class for factory method pattern"""

    @abstractmethod
    def create_request(self, data):
        """Create request object"""
        pass


class RegistrationRequestCreator(RequestCreatorInterface):
    """Create RegistrationRequest object"""

    def create_request(self, data):
        return RegistrationRequest(data)


class LoginRequestCreator(RequestCreatorInterface):
    """Create RegistrationRequest object"""

    def create_request(self, data):
        return LoginRequest(data)


class ChatRequestCreator(RequestCreatorInterface):
    """Create ChatRequest object"""

    def create_request(self, data):
        return ChatRequest(data)
