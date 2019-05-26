import sys
from typing import Dict
from PyQt5.QtCore import (
    Qt,
    QThread,
    pyqtSignal
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QDesktopWidget,
    QTextEdit,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel
)
from core import (
    Server,
)
from observers import (
    ServerStatusListener,
    LogListener,
    ClientListener
)


class ServerThread(QThread):

    def __init__(self, server):
        self.server = server
        super().__init__()

    def run(self):
        self.server()


class TitleMixin:
    """Adds title field to widgets for making them more identicable"""

    def __init__(self, title=None):
        self.title = title
        super().__init__()


class TitledLineEdit(TitleMixin, QLineEdit):
    """QLineEdit with 'title' field"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FormFactory(QFormLayout):
    """
    Custom form layout for simplefied form creation process.
    Accepts in constructor or sets 'field' names and then creates rows.
    Fields passed as 'fields=[...]'.
    Number of rows - len(fields).
    Format of row: <field> QLabel - <field> TitledLineEdit.
    """

    def __init__(self, *ars, **kwargs):
        super().__init__()
        self.fields = self.adapter(kwargs.get('fields'))

    def adapter(self, structure) -> Dict:
        if type(structure) is not dict:
            return {element: None for element in structure}
        return structure

    def construct(self) -> None:
        for field, value in self.fields.items():

            line_edit = TitledLineEdit(title=field)

            line_edit.setAlignment(Qt.AlignCenter)

            if value:
                line_edit.setText(str(value))

            self.addRow(
                QLabel(
                    field.replace('_', ' ').title()
                ), line_edit
            )


class ServerGui(QWidget):

    server = Server()
    append_log = pyqtSignal(str)
    append_client = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

        self.append_log.connect(self.log_text_edit.append)
        self.append_client.connect(self.clients_text_edit.append)

        self.log_listener = LogListener(self, self.server.notifier, 'log')
        self.client_listener = ClientListener(
            self, self.server.notifier, 'client'
        )
        self.server_listener = ServerStatusListener(
            self, self.server.notifier, 'state'
        )

        self.server_listener.refresh(self.server.notifier)

    def init_ui(self):

        titles = {
            'state': self.server.state,
            'host': self.server.settings.host,
            'port': self.server.settings.port,
            'buffer_size': self.server.settings.buffer_size,
            'encoding_name': self.server.settings.encoding_name,
            'connections': self.server.settings.connections
        }

        settings_form_layout = FormFactory(fields=titles)
        settings_form_layout.construct()

        self.settings_group = QGroupBox('Settings')
        self.settings_group.setFixedWidth(250)
        self.settings_group.setLayout(settings_form_layout)

        self.run_server_btn = QPushButton('Run server')
        self.run_server_btn.setObjectName('run_server_btn')
        self.run_server_btn.clicked.connect(self.run_server)

        self.stop_server_btn = QPushButton('Stop server')
        self.stop_server_btn.setObjectName('stop_server_btn')
        self.stop_server_btn.setDisabled(True)
        self.stop_server_btn.clicked.connect(self.stop_server)

        v_settings_layout = QVBoxLayout()
        v_settings_layout.addWidget(self.settings_group)
        v_settings_layout.addWidget(self.run_server_btn)
        v_settings_layout.addWidget(self.stop_server_btn)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)

        v_log_layout = QVBoxLayout()
        v_log_layout.addWidget(self.log_text_edit)

        self.log_group = QGroupBox('Log')
        self.log_group.setLayout(v_log_layout)

        self.clients_text_edit = QTextEdit()
        self.clients_text_edit.setReadOnly(True)

        v_clients_layout = QVBoxLayout()
        v_clients_layout.addWidget(self.clients_text_edit)

        self.clients_group = QGroupBox('Clients')
        self.clients_group.setLayout(v_clients_layout)

        h_layout = QHBoxLayout()
        h_layout.addLayout(v_settings_layout)
        h_layout.addWidget(self.log_group)
        h_layout.addWidget(self.clients_group)

        self.setWindowTitle('Admin panel')
        self.setLayout(h_layout)
        self.resize(900, 300)
        self.setFixedSize(self.size())
        self.to_center()
        self.show()

    def to_center(self):
        """
        Gets geometry of app window, positions it on the center of the screen
        and then moves app window to it
        """

        rectangle = self.frameGeometry()
        desktop_center = QDesktopWidget().availableGeometry().center()
        rectangle.moveCenter(desktop_center)
        self.move(rectangle.topLeft())

    def run_server(self):

        widgets = self.settings_group.findChildren(TitledLineEdit)
        settings = {
            widget.title: (
                widget.text()
                if widget.title not in ('port', 'connections')
                else int(widget.text())
            )
            for widget in widgets
        }
        self.server.settings.update(settings)

        self.run_thread = ServerThread(self.server)
        self.run_thread.start()

    def stop_server(self):
        self.server.close()

    def closeEvent(self, event):
        if self.server.state == 'Connected':
            self.server.close()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ServerGui()
    sys.exit(app.exec_())
