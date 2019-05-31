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
        print(event)
        print(self._listeners)

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
    def refresh(self, notifier: Notifier = None, *args, **kwargs) -> None:
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


class ResponseListener(Listener):
    """
    Listener that updates status log line edit fields
    on 'StatusGroup' custom widget by response status code and info message.
    """

    event = 'response'

    def refresh(self, *args, **kwargs):
        print(self.employer.status_log_code)
        self.employer.status_log_code.setText(
            f"{kwargs.get('code')}"
        )
        self.employer.status_log_info.setText(
            f"{kwargs.get('info')}"
        )


class LoginListener(Listener):

    event = 'response'

    def refresh(self, *args, **kwargs) -> None:

        if kwargs.get('action') == 'login' and kwargs.get('code') == 200:
            self.employer.parent.chat.emit(kwargs)
            # self.employer.close_window.emit()


class ChatListener(Listener):

    event = 'chat'

    def refresh(self, *args, **kwargs) -> None:
        pass
        # if kwargs.get('code') == 200:

