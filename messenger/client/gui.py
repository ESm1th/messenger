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

from settings import (
    HOST,
    PORT,
    BUFFER_SIZE,
    ENCODING_NAME,
    BASE_DIR
)


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


class Form(QFormLayout):
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

    def construct(self):
        for field, value in self.fields.items():

            line_edit = TitledLineEdit(title=field)

            if value:
                line_edit.setText(value)
                line_edit.setAlignment(Qt.AlignCenter)

            self.addRow(QLabel(field), line_edit)


class StatusBar(QStatusBar):
    """Base status bar widget"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listener = StatusBarListener(self, Client().notifier)
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(20)
        self.setStyleSheet(
            """
            QStatusBar {\
                background-color: #C8C8C8;\
                border-top: 2px black solid;\
                }
            """
        )

        status_label = QLabel('Status:')
        self.connection = QLabel('Disconnected')

        host_label = QLabel('Ip address:')
        self.host = QLabel()

        port_label = QLabel('Port number:')
        self.port = QLabel()

        self.addPermanentWidget(status_label)
        self.addPermanentWidget(self.connection)
        self.addPermanentWidget(host_label)
        self.addPermanentWidget(self.host)
        self.addPermanentWidget(port_label)
        self.addPermanentWidget(self.port)

        self.setSizeGripEnabled(False)


class ClientGui(QWidget):
    """Client application base window"""

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
        image = QPixmap(os.path.join(BASE_DIR, 'media/Chat.png'))
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

        dialog = RegistrationForm()
        self.setVisible(False)
        dialog.exec_()
        self.setVisible(True)

    def settings_dialog(self):
        """Opens settings dialog form"""

        dialog = SettingsForm()
        self.setVisible(False)
        dialog.exec_()
        self.setVisible(True)


class SettingsForm(QDialog):

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):

        titles = {
            'host': str(HOST),
            'port': str(PORT),
            'buffer': str(BUFFER_SIZE),
            'encoding': str(ENCODING_NAME)
        }

        layout = Form(fields=titles)
        layout.construct()

        confirm_button = QPushButton('Confirm')
        default_button = QPushButton('Set default')
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)

        v_layout = QVBoxLayout()
        v_layout.addLayout(layout)
        v_layout.addWidget(confirm_button)
        v_layout.addWidget(default_button)
        v_layout.addWidget(cancel_button)

        self.setLayout(v_layout)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Settings')
        self.setModal(True)


class RegistrationForm(QDialog):

    request_creator = RegistrationRequestCreator()

    def __init__(self):
        self.listener = RegistrationFormListener(self, Client().notifier)
        super().__init__()
        self.init_ui()

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

        self.username_la = QLabel('Username')
        self.username_le = TitledLineEdit(title='username')

        self.first_name_la = QLabel('First name')
        self.first_name_le = TitledLineEdit(title='first_name')

        self.second_name_la = QLabel('Second name')
        self.second_name_le = TitledLineEdit('second_name')

        self.email_la = QLabel('Email')
        self.email_le = TitledLineEdit('email')

        self.phone_la = QLabel('Phone')
        self.phone_le = TitledLineEdit('phone')

        self.password_la = QLabel('Password')
        self.password_le = TitledLineEdit('password')

        self.reapeat_password_la = QLabel('Repeat password')
        self.reapeat_password_le = TitledLineEdit('repeat_password')

        form_layout = QFormLayout()
        form_layout.addRow(self.username_la, self.username_le)
        form_layout.addRow(self.first_name_la, self.first_name_le)
        form_layout.addRow(self.second_name_la, self.second_name_le)
        form_layout.addRow(self.email_la, self.email_le)
        form_layout.addRow(self.phone_la, self.phone_le)
        form_layout.addRow(self.password_la, self.password_le)
        form_layout.addRow(
            self.reapeat_password_la, self.reapeat_password_le
        )

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
        raw_data = request.prepare()

        send_thread = threading.Thread(
            target=Client().send_request(raw_data)
        )
        send_thread.start()


if __name__ == '__main__':
    app = QApplication([])
    widget = ClientGui()
    sys.exit(app.exec_())
