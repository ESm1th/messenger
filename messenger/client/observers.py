from abc import ABC, abstractmethod
from typing import Dict


class Notifier(ABC):
    """Notifier interface"""

    _state: bool = False

    def __init__(self, obj) -> None:
        self.employer = obj

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


class BaseNotifier(Notifier):

    _listeners: Dict = {}

    def add_listener(self, event: str, listener: 'Listener') -> None:
        """Adds listener to notifier"""

        if event in self._listeners:
            self._listeners[event].append(listener)
        else:
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

    event: str

    def __init__(self, obj, notifier):
        self.employer = obj
        notifier.add_listener(self.event, self)

    @abstractmethod
    def refresh(self, *args, **kwargs) -> None:
        pass


class StateListener(Listener):
    """
    Listener that updates status bar fields by
    response status code and info message.
    """

    event = 'state'

    def refresh(self, notifier):
        self.employer.showMessage(
            'Connected' if notifier.employer.state else 'Disconnected'
        )


class StatusListener(Listener):
    """
    Listener sets attributes to class 'core.Status' from response status code
    and info message.
    """

    event = 'response'

    def refresh(self, *args, **kwargs):
        self.employer.update(**kwargs)


class StatusGroupListener(Listener):

    event = 'response'

    def refresh(self, *args, **kwargs):
        self.employer.update()


class LoginListener(Listener):

    event = 'response'

    def refresh(self, *args, **kwargs) -> None:

        if kwargs.get('action') == 'login' and kwargs.get('code') == 200:
            self.employer.parent.chat.emit(kwargs)
            self.employer.close_window.emit()


class ContactListener(Listener):

    event = 'response'

    def refresh(self, *args, **kwargs) -> None:

        if kwargs.get('code') == 200:

            if kwargs.get('action') == 'add_contact':
                self.employer.update_model_add.emit(kwargs.get('new_contact'))

            elif kwargs.get('action') == 'delete_contact':
                self.employer.update_model_delete.emit(kwargs.get('contact'))


class ChatListener(Listener):

    event = 'response'

    def refresh(self, *args, **kwargs) -> None:

        if kwargs.get('code') == 200:

            if kwargs.get('action') == 'get_chat':
                self.employer.open_chat.emit(kwargs)


class NewMessageListener(Listener):

    event = 'response'

    def refresh(self, *args, **kwargs) -> None:

        if kwargs.get('code') == 200:

            if kwargs.get('action') == 'add_message':

                if self.employer.active_chat == kwargs.get('chat_id'):

                    if kwargs.get('message'):
                        self.employer.append_messages_to_textbox.emit(
                            kwargs.get('messages')
                        )
