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


class ClientNotifier(Notifier):

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


class StatusBarListener(Listener):
    """
    Listener that updates status bar fields by
    response status code and info message.
    """

    def __init__(self, obj, notifier):
        self.employer = obj
        notifier.add_listener('settings', self)
        super().__init__()

    def refresh(self, notifier):
        if notifier.employer.state:
            self.employer.connection.setText('Connected')
        else:
            self.employer.connection.setText('Disconnected')
        self.employer.host.setText(str(notifier.employer.host))
        self.employer.port.setText(str(notifier.employer.port))


class RegistrationFormListener(Listener):
    """
    Listener that updates status log line edit fields
    on 'Registration Form' widget by response status code and info message.
    """

    def __init__(self, obj, notifier):
        self.object = obj
        notifier.add_listener('response', self)
        super().__init__()

    def refresh(self, *args, **kwargs):

        self.object.status_log_code.setText(
            f"{kwargs.get('code')}"
        )
        self.object.status_log_info.setText(
            f"{kwargs.get('info')}"
        )
