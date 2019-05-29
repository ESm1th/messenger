import sys
import os
import threading
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QDialog,
    QDesktopWidget,
    QStatusBar,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox
)
from PyQt5.QtGui import (
    QPixmap
)
from PyQt5.QtCore import (
    Qt,
    QThread,
    pyqtSignal
)
from typing import Dict

from core import Client
from requests import (
    RegistrationRequestCreator,
)
from observers import (
    StatusBarListener,
    RegistrationFormListener
)

import settings


class TitleMixin:
    """Adds title field to widgets for making them more identicable"""

    def __init__(self, title=None):
        self.title = title
        super().__init__()


class TitledLineEdit(TitleMixin, QLineEdit):
    """QLineEdit with 'title' field"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MainWindowButton(QPushButton):
    """Main window buttons type with fixed size"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(200, 40)


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

            if value:
                line_edit.setText(str(value))
                line_edit.setAlignment(Qt.AlignCenter)

            self.addRow(QLabel(field.replace('_', ' ').title()), line_edit)


class StatusBar(QStatusBar):
    """Base status bar widget"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listener = StatusBarListener(self, Client().notifier)
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(20)
        self.setSizeGripEnabled(False)
        self.setStyleSheet(
            """
            QStatusBar {\
                background-color: #C8C8C8;\
                border-top: 2px black solid;\
                }
            """
        )
        self.showMessage(f'Status...')


class ClientGui(QWidget):
    """Client application base window"""

    client = Client()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.register_button = MainWindowButton('Registration')
        self.register_button.clicked.connect(self.register_dialog)

        self.login_button = MainWindowButton('Log in')

        self.settings_button = MainWindowButton('Settings')
        self.settings_button.clicked.connect(self.settings_dialog)

        self.status_bar = StatusBar()

        v_layout = QVBoxLayout()
        v_layout.setAlignment(Qt.AlignCenter)
        v_layout.setSpacing(15)
        v_layout.setContentsMargins(30, 0, 0, 0)
        v_layout.addWidget(self.register_button)
        v_layout.addWidget(self.login_button)
        v_layout.addWidget(self.settings_button)

        image_label = QLabel('Image')
        image_label.setFixedSize(200, 200)
        image = QPixmap(os.path.join(settings.BASE_DIR, 'media/Chat.png'))
        image_label.setPixmap(image)
        image_label.setScaledContents(True)

        h_layout = QHBoxLayout()
        h_layout.addLayout(v_layout)
        h_layout.addWidget(image_label)
        h_layout.setSpacing(40)
        h_layout.setContentsMargins(0, 0, 30, 10)

        main_v_layout = QVBoxLayout()
        main_v_layout.setContentsMargins(0, 20, 0, 0)
        main_v_layout.addLayout(h_layout)
        main_v_layout.addWidget(self.status_bar)

        self.setLayout(main_v_layout)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Geek-messenger')
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

    def register_dialog(self):
        """Opens registration dialog form"""

        dialog = RegistrationForm(self.client)
        self.setVisible(False)
        dialog.exec_()
        self.setVisible(True)

    def settings_dialog(self):
        """Opens settings dialog form"""

        dialog = SettingsForm(self.client)
        self.setVisible(False)
        dialog.exec_()
        self.setVisible(True)


class SettingsForm(QDialog):

    def __init__(self, client):
        super().__init__()
        self.settings = client.settings
        self.init_ui()

    def init_ui(self):

        titles = {
            'host': self.settings.host,
            'port': self.settings.port,
            'buffer_size': self.settings.buffer_size,
            'encoding_name': self.settings.encoding_name
        }

        settings_layout = FormFactory(fields=titles)
        settings_layout.construct()

        confirm_button = QPushButton('Confirm')
        confirm_button.clicked.connect(self.update_settings)

        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.close)

        v_layout = QVBoxLayout()
        v_layout.addLayout(settings_layout)
        v_layout.addWidget(confirm_button)
        v_layout.addWidget(cancel_button)

        self.setLayout(v_layout)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Settings')
        self.setModal(True)

    def update_settings(self):
        widgets = self.findChildren(TitledLineEdit)

        new_settings = {
            widget.title: (
                widget.text()
                if widget.title not in ('port', 'buffer_size')
                else int(widget.text())
            )
            for widget in widgets
        }
        self.settings.update(new_settings)

        self.close()


class RegistrationForm(QDialog):

    request_creator = RegistrationRequestCreator()
    change_state = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.listener = RegistrationFormListener(self, self.client.notifier)
        self.init_ui()
        self.change_state.connect(self.client.set_state)


    def init_ui(self):

        self.status_log_code = QLineEdit()
        self.status_log_code.setPlaceholderText('Response code...')
        self.status_log_code.setReadOnly(True)

        self.status_log_info = QLineEdit()
        self.status_log_info.setPlaceholderText('Response status...')
        self.status_log_info.setReadOnly(True)

        status_log_group = QGroupBox('Status log')
        status_log_layout = QVBoxLayout()
        status_log_layout.addWidget(self.status_log_code)
        status_log_layout.addWidget(self.status_log_info)
        status_log_group.setLayout(status_log_layout)

        titles = (
            'username',
            'password',
            'repeat_password'
        )

        form_layout = FormFactory(fields=titles)
        form_layout.construct()

        self.confirm_button = QPushButton('Send')
        self.confirm_button.clicked.connect(self.send_registration_request)

        self.cancel_button = QPushButton('Exit')
        self.cancel_button.clicked.connect(self.reject)

        user_data_group = QGroupBox('User data')
        user_data_group.setLayout(form_layout)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.confirm_button)
        h_layout.addWidget(self.cancel_button)
        buttons_group = QGroupBox('Send or cancel')
        buttons_group.setLayout(h_layout)

        v_layout = QVBoxLayout()
        v_layout.addWidget(status_log_group)
        v_layout.addWidget(user_data_group)
        v_layout.addWidget(buttons_group)

        self.setLayout(v_layout)
        self.setWindowTitle('Register form')
        self.setModal(True)

    def send_registration_request(self):
        widgets = self.findChildren(TitledLineEdit)

        user_data = {
            widget.title: widget.text().strip()
            for widget in widgets
        }

        request = self.request_creator.create_request(user_data)
        raw_data = request.prepare().encode(self.client.settings.encoding_name)
        self.client.connect()

        # response_thread = threading.Thread(target=self.client.get_response)
        # response_thread.start()
        send_thread = threading.Thread(target=self.client.send_request, args=(raw_data,))
        send_thread.start()
        send_thread.join()
        
        print(self.client.socket.fileno())
        self.change_state.emit('Disconnected')
        print(self.client.state)
        self.client.close()
        print('after close')


if __name__ == '__main__':
    app = QApplication([])
    widget = ClientGui()
    sys.exit(app.exec_())
