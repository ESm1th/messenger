from abc import ABC, abstractmethod
from typing import Dict
from logging import getLogger


logger = getLogger('server_logger')


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


class Listener(ABC):
    """Listener interface"""

    def __init__(self, obj, notifier, event):
        self.employer = obj
        notifier.add_listener(event, self)
        super().__init__()

    @abstractmethod
    def refresh(self, notifier: Notifier = None, *args, **kwargs) -> None:
        pass


class BaseNotifier(Notifier):

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


class ServerStatusListener(Listener):

    def refresh(self, notifier: Notifier, *args, **kwargs):
        """
        Updates 'TitledLineEdit' widgets in 'settings_group' widget.
        Makes 'state' line edit widget 'read only' always.
        Other widgets change their behavior by servers 'state' attribute value.
        If server 'state' is 'connected' - all other widgets
        become 'read only'.
        If server 'state' is 'connected' - all other
        widgets become 'read only'.
        If server 'state' is 'disconnected' - all other
        widgets become 'writable'.
        """

        state = notifier.employer.state
        widgets = self.employer.settings_group.children()

        for widget in widgets:

            if state == 'Connected':
                self.employer.run_server_btn.setDisabled(True)
                self.employer.stop_server_btn.setDisabled(False)

                if hasattr(widget, 'title'):
                    if widget.title == 'state':
                        widget.setText(state)
                    widget.setReadOnly(True)
            else:
                self.employer.run_server_btn.setDisabled(False)
                self.employer.stop_server_btn.setDisabled(True)

                if hasattr(widget, 'title'):
                    if widget.title == 'state':
                        widget.setText(state)
                    else:
                        widget.setReadOnly(False)


class LogListener(Listener):

    def refresh(self, notifier: Notifier, *args, **kwargs) -> None:
        log = kwargs.get('info')
        if log:
            self.employer.append_log.emit(log)


class RequestListener(Listener):

    def refresh(self, notifier: Notifier, *args, **kwargs) -> None:
        request = kwargs.get('request')
        if request:
            self.employer.write_request.emit(request)


class ResponseListener(Listener):

    def refresh(self, notifier: Notifier, *args, **kwargs) -> None:
        response = kwargs.get('response')
        if response:
            self.employer.write_response.emit(response)    


class ClientListener(Listener):

    def refresh(self, notifier: Notifier, *args, **kwargs) -> None:

        action = kwargs.get('action')
        data = kwargs.get('data')

        if data:
            if action == 'add':
                self.employer.update_model_add.emit(data)
            elif action == 'delete':
                self.employer.update_model_delete.emit(data)
