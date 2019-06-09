from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict
import json


class RequestInterface:
    """Interface for all request objects"""

    action: str = None
    """Used by server to define appropriate controller"""

    timestamp: float = datetime.now().timestamp()
    data: Dict = {}

    def __init__(self, user_data: Dict = {}) -> None:
        """
        Clears class attribute `data` if it contains any data.
        Updates it with data dictionary passed as argument.
        """
        if bool(self.data):
            self.data.clear()

        self.data.update(
            {'action': self.action, 'time': self.timestamp, 'data': user_data}
        )

    def prepare(self) -> str:
        """Returns `json` string from passed `data` dictionary attribute."""
        raw_data = json.dumps(self.data)
        return raw_data


class RegistrationRequest(RequestInterface):
    """Class represents request objects for registration"""

    action = 'register'


class LoginRequest(RequestInterface):
    """Class represents request objects for logging on server"""

    action = 'login'


class ChatRequest(RequestInterface):
    """Class represents request objects for activating chat"""

    action = 'get_chat'


class MessageRequest(RequestInterface):
    """Class represents request objects for adding message to chat"""

    action = 'add_message'


class MessageListenRequest(RequestInterface):
    """
    Class represents request objects for
    listening changes in chat messages.
    """

    action = 'message_listener'


class AddContactRequest(RequestInterface):
    """Class represents request objects for adding contact to contact list"""

    action = 'add_contact'


class DeleteContactRequest(RequestInterface):
    """
    Class represents request objects for
    deleting contact from contact list.
    """

    action = 'delete_contact'


class RequestCreatorInterface(ABC):
    """Abstract base class for factory method pattern"""

    @abstractmethod
    def create_request(self, data: Dict) -> RequestInterface:
        """Create request object"""
        pass


class RegistrationRequestCreator(RequestCreatorInterface):
    """Create RegistrationRequest object"""

    def create_request(self, data: Dict) -> RegistrationRequest:
        return RegistrationRequest(data)


class LoginRequestCreator(RequestCreatorInterface):
    """Create RegistrationRequest object"""

    def create_request(self, data: Dict) -> LoginRequest:
        return LoginRequest(data)


class ChatRequestCreator(RequestCreatorInterface):
    """Create ChatRequest object"""

    def create_request(self, data: Dict) -> ChatRequest:
        return ChatRequest(data)


class AddContactRequestCreator(RequestCreatorInterface):
    """Create AddContactRequest object"""

    def create_request(self, data: Dict) -> AddContactRequest:
        return AddContactRequest(data)


class DeleteContactRequestCreator(RequestCreatorInterface):
    """Create DeleteContactRequest object"""

    def create_request(self, data: Dict) -> DeleteContactRequest:
        return DeleteContactRequest(data)


class MessageRequestCreator(RequestCreatorInterface):
    """Create MessageRequest object"""

    def create_request(self, data: Dict) -> MessageRequest:
        return MessageRequest(data)


class MessageListenRequestCreator(RequestCreatorInterface):

    def create_request(self, data: Dict) -> MessageListenRequest:
        """Create MessageListenRequest object"""

        return MessageListenRequest(data)
