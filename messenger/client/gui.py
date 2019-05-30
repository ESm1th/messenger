import sys
import os
import threading
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QDialog,
    QDesktopWidget,
    QMdiArea,
    QStatusBar,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QTextEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QColumnView
)
from PyQt5.QtGui import (
    QPixmap,
    QStandardItemModel,
    QStandardItem
)
from PyQt5.QtCore import (
    Qt,
    QThread,
    QStringListModel,
    pyqtSignal
)
from typing import Dict

from core import Client
from requests import (
    RegistrationRequestCreator,
    LoginRequestCreator,
    ChatRequestCreator
)
from observers import (
    StateListener,
    ResponseListener,
    LoginListener
)

import settings


class ClientThread(QThread):

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        self.client.connect()


class ChatThread(QThread):

    def __init__(self, widget):
        super().__init__()
        self.widget = widget
    
    def run(self):
        self.widget()


class TitleMixin:
    """Adds title field to widgets for making them more identicable"""

    def __init__(self, title=None):
        self.title = title
        super().__init__()


class CenterMixin:

    def to_center(self):
        """
        Gets geometry of window, positions it on the center of the screen
        and then moves app window to it
        """

        rectangle = self.frameGeometry()
        desktop_center = QDesktopWidget().availableGeometry().center()
        rectangle.moveCenter(desktop_center)
        self.move(rectangle.topLeft())


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


class StatusGroup(QGroupBox):
    """
    Custom 'group box' widget.
    Prints 'status code' and 'info message' for responses.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.listener = ResponseListener(
            self, kwargs.get('notifier')
        )
        self.construct()

    def construct(self):
        self.status_log_code = QLineEdit()
        self.status_log_code.setPlaceholderText('Response code...')
        self.status_log_code.setReadOnly(True)

        self.status_log_info = QLineEdit()
        self.status_log_info.setPlaceholderText('Response status...')
        self.status_log_info.setReadOnly(True)

        status_log_layout = QVBoxLayout()
        status_log_layout.addWidget(self.status_log_code)
        status_log_layout.addWidget(self.status_log_info)
        self.setLayout(status_log_layout)


class StatusBar(QStatusBar):
    """Base status bar widget"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.listener = StateListener(
            self, kwargs.get('notifier')
        )
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


class RegistrationForm(QDialog):

    request_creator = RegistrationRequestCreator()

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.init_ui()

    def init_ui(self):

        status_box = StatusGroup('Status log', notifier=self.client.notifier)

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
        v_layout.addWidget(status_box)
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

        send_thread = threading.Thread(
            target=self.client.send_request, args=(raw_data,)
        )
        send_thread.start()


class LoginForm(QDialog):

    request_creator = LoginRequestCreator()
    close_window = pyqtSignal()

    def __init__(self, client, parent):
        super().__init__()
        self.client = client
        self.parent = parent
        self.listener = LoginListener(self, self.client.notifier)
        self.close_window.connect(self.close)
        self.init_ui()

    def init_ui(self):

        status_box = StatusGroup('Status log', notifier=self.client.notifier)

        titles = (
            'username',
            'password'
        )

        login_form_layout = FormFactory(fields=titles)
        login_form_layout.construct()

        credentials = QGroupBox('Credentials')
        credentials.setLayout(login_form_layout)

        self.confirm_button = QPushButton('Send')
        self.confirm_button.clicked.connect(self.send_login_request)

        self.cancel_button = QPushButton('Exit')
        self.cancel_button.clicked.connect(self.close)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.confirm_button)
        h_layout.addWidget(self.cancel_button)

        buttons_group = QGroupBox('Send or cancel')
        buttons_group.setLayout(h_layout)

        v_box_layout = QVBoxLayout()
        v_box_layout.addWidget(status_box)
        v_box_layout.addWidget(credentials)
        v_box_layout.addWidget(buttons_group)

        self.setLayout(v_box_layout)
        self.setWindowTitle('Login form')

    def send_login_request(self):
        widgets = self.findChildren(TitledLineEdit)

        user_data = {
            widget.title: widget.text().strip()
            for widget in widgets
        }

        request = self.request_creator.create_request(user_data)
        raw_data = request.prepare().encode(self.client.settings.encoding_name)

        send_thread = threading.Thread(
            target=self.client.send_request, args=(raw_data,)
        )
        send_thread.start()


class SettingsForm(QWidget):

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


class ChatWindow(QDialog):

    request_creator = ChatRequestCreator()

    def __init__(self, contacts):
        super().__init__()
        self.chats_data = {}
        self.contacts = contacts
        self.init_model()
        self.init_ui()

    def init_model(self):
        self.model = QStringListModel(self.contacts)

    def init_ui(self):
        column_view = QColumnView()
        column_view.setModel(self.model)
        column_view.setFixedWidth(100)
        column_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        column_view.doubleClicked.connect(self.send_chat_request)

        lbl_contacts = QLabel('Contacts')

        btn_add_contact = QPushButton('Add contact')

        v_contacts_layout = QVBoxLayout()
        v_contacts_layout.addWidget(lbl_contacts)
        v_contacts_layout.addWidget(column_view)
        v_contacts_layout.addWidget(btn_add_contact)

        lbl_chat = QLabel('Chat window')
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setDisabled(True)

        lbl_enter = QLabel('Enter message')
        self.message_line_edit = QLineEdit()

        v_chat_layout = QVBoxLayout()
        v_chat_layout.addWidget(lbl_chat)
        v_chat_layout.addWidget(self.chat_text_edit)
        v_chat_layout.addWidget(lbl_enter)
        v_chat_layout.addWidget(self.message_line_edit)

        h_box_layout = QHBoxLayout()
        h_box_layout.addLayout(v_contacts_layout)
        h_box_layout.addLayout(v_chat_layout)

        self.setLayout(h_box_layout)
        self.resize(700, 500)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Chat')

    def send_chat_request(self, item):

        request = self.request_creator.create_request(
            {'contact_username': item.data()}
        )
        raw_data = request.prepare().encode(self.client.settings.encoding_name)

        send_thread = threading.Thread(
            target=self.client.send_request, args=(raw_data,)
        )
        send_thread.start()


class ClientGui(CenterMixin, QWidget):
    """Client application base window"""

    client = Client()
    chat = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.chat.connect(self.chat_window)
        self.client_thread = ClientThread(self.client)
        self.client_thread.start()

    def init_ui(self):
        self.register_button = MainWindowButton('Registration')
        self.register_button.clicked.connect(self.register_dialog)

        self.login_button = MainWindowButton('Log in')
        self.login_button.clicked.connect(self.login_dialog)

        self.settings_button = MainWindowButton('Settings')
        self.settings_button.clicked.connect(self.settings_dialog)

        self.status_bar = StatusBar(notifier=self.client.notifier)

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

    def register_dialog(self):
        """Opens registration dialog form"""

        dialog = RegistrationForm(self.client)
        self.setVisible(False)
        dialog.exec_()
        self.setVisible(True)

    def login_dialog(self):
        dialog = LoginForm(self.client, self)
        self.setVisible(False)
        dialog.exec_()
        self.setVisible(True)

    def settings_dialog(self):
        """Opens settings dialog form"""

        dialog = SettingsForm(self.client)
        self.setVisible(False)
        dialog.exec_()
        self.setVisible(True)

    def chat_window(self, contacts):
        dialog = ChatWindow(contacts)
        self.setVisible(False)
        dialog.exec_()
        self.setVisible(True)


if __name__ == '__main__':
    app = QApplication([])
    widget = ChatWindow()
    sys.exit(app.exec_())
