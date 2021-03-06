import sys
import os
import threading
from typing import Dict
from io import BytesIO

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
    QTextEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QColumnView,
    QToolBar,
    QAction,
    QFileDialog
)
from PyQt5.QtGui import (
    QPixmap,
    QFont,
    QIcon
)
from PyQt5.QtCore import (
    Qt,
    QThread,
    QStringListModel,
    pyqtSignal
)

from PIL import Image
from PIL.ImageQt import ImageQt

from core import (
    Client,
    FtpClient,
    Sender
)

from observers import (
    StateListener,
    StatusGroupListener,
    LoginListener,
    ContactListener,
    ChatListener,
    NewMessageListener,
    ProfileListener,
    AvatarListener,
    SearchMessageListener
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

            if 'password' in field:
                line_edit.setEchoMode(QLineEdit.Password)

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
        self.client = kwargs.get('client')
        self.listener = StatusGroupListener(self, self.client.notifier)
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

    def update(self):
        self.status_log_code.setText(self.client.status.code or None)
        self.status_log_info.setText(self.client.status.info or None)

    def clear(self):
        self.status_log_code.clear()
        self.status_log_info.clear()


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


class CommonMixin:

    clear_status_content = pyqtSignal()

    def __init__(self, **kwargs):
        super().__init__()
        self.client = kwargs.get('client')
        self.parent = kwargs.get('parent')

    def show(self):
        if hasattr(self, 'status_group'):
            self.clear_status_content.connect(self.status_group.clear)
            self.clear_status_content.emit()
        super().show()

    def closeEvent(self, event):
        if self.parent:
            self.parent.show()
        event.accept()


class RegistrationForm(CommonMixin, QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sender = Sender(self.client)
        self.init_ui()

    def init_ui(self):

        self.status_group = StatusGroup('Status log', client=self.client)

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
        self.cancel_button.clicked.connect(self.close)

        user_data_group = QGroupBox('User data')
        user_data_group.setLayout(form_layout)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.confirm_button)
        h_layout.addWidget(self.cancel_button)
        buttons_group = QGroupBox('Send or cancel')
        buttons_group.setLayout(h_layout)

        v_layout = QVBoxLayout()
        v_layout.addWidget(self.status_group)
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

        self._sender.send_request(action='register', user_data=user_data)


class LoginForm(CommonMixin, QDialog):

    close_window = pyqtSignal()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sender = Sender(self.client)
        self.listener = LoginListener(self, self.client.notifier)
        self.init_ui()
        self.close_window.connect(self.close)

    def init_ui(self):

        self.status_group = StatusGroup('Status log', client=self.client)

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
        v_box_layout.addWidget(self.status_group)
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

        self._sender.send_request(action='login', user_data=user_data)

    def closeEvent(self, event):
        if not self.sender().__class__ is type(self):
            self.parent.show()
        event.accept()


class SettingsForm(CommonMixin, QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = self.client.settings
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
        self.client.close()
        self.settings.update(new_settings)

        self.client_thread = ClientThread(self.client)
        self.client_thread.start()

        self.close()


class ProfileForm(CommonMixin, QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sender = Sender(self.client)
        self.ftp_client = FtpClient()
        self.profile_data = kwargs
        self.init_ui()

    def init_ui(self):
        self.avatar_picture = QLabel('None')
        self.avatar_picture.setAlignment(Qt.AlignCenter)

        file_name = self.profile_data.get('file_name')

        if file_name:
            self.ftp_client.connect()
            data = self.ftp_client.download_file(file_name)

            if data:
                pixmap = QPixmap()
                pixmap.loadFromData(data.getvalue())
                self.avatar_picture.setPixmap(pixmap)
            else:
                self.avatar_picture.setText(
                    'Error has occurred when downloading avatar'
                )

        v_avatar_layout = QVBoxLayout()
        v_avatar_layout.addWidget(self.avatar_picture)
        v_avatar_layout.setAlignment(Qt.AlignCenter)

        avatar_group = QGroupBox('Avatar')
        avatar_group.setLayout(v_avatar_layout)
        avatar_group.setFixedWidth(300)

        titles = {
            'first_name': self.profile_data.get('first_name'),
            'second_name': self.profile_data.get('second_name'),
        }

        profile_form_layout = FormFactory(fields=titles)
        profile_form_layout.construct()
        profile_form_layout.setFormAlignment(Qt.AlignCenter)
        profile_form_layout.setSpacing(10)

        profile_group = QGroupBox('Profile data')
        profile_group.setLayout(profile_form_layout)

        [
            (
                line.setAlignment(Qt.AlignLeft),
                line.setTextMargins(10, 0, 10, 0)
            )
            for line in profile_group.findChildren(TitledLineEdit)
        ]

        get_avatar_button = QPushButton('Choose avatar')
        get_avatar_button.setFixedHeight(40)
        get_avatar_button.clicked.connect(self.avatar_file_dialog)

        update_data_button = QPushButton('Submit')
        update_data_button.setFixedHeight(40)
        update_data_button.clicked.connect(self.send_update_profile_request)

        v_box_profile_layout = QVBoxLayout()
        v_box_profile_layout.addWidget(profile_group)
        v_box_profile_layout.addWidget(get_avatar_button)
        v_box_profile_layout.addWidget(update_data_button)

        h_box_layout = QHBoxLayout()
        h_box_layout.addWidget(avatar_group)
        h_box_layout.addLayout(v_box_profile_layout)

        self.setLayout(h_box_layout)
        self.setWindowTitle('Profile data')
        self.setFixedHeight(300)
        self.setFixedWidth(600)
        self.show()

    def avatar_file_dialog(self):
        needed_size = 250, 250

        self.image_path = QFileDialog.getOpenFileName(
            self, 'Open file', '/home'
        )[0]
        image = Image.open(self.image_path)

        image.thumbnail(
            needed_size, Image.ANTIALIAS
        )

        image_temp = ImageQt(image.convert('RGBA'))
        pixmap = QPixmap.fromImage(image_temp)
        self.avatar_picture.setPixmap(pixmap)

    def send_update_profile_request(self):
        widgets = self.findChildren(TitledLineEdit)

        user_data = {
            widget.title: widget.text().strip()
            for widget in widgets
        }

        user_data.update(
            {'username': self.profile_data.get('username')}
        )

        if hasattr(self, 'image_path'):
            image = Image.open(self.image_path)
            image = image.resize((80, 80), Image.ANTIALIAS)
            image_bytes = BytesIO()
            image.save(image_bytes, 'png')
            image_bytes.seek(0)

            self.ftp_client.connect()
            username = self.profile_data.get('username')
            upload_status = self.ftp_client.upload_file(
                f'{username}_avatar.png', image_bytes
            )

            user_data.update(
                {'upload_status': upload_status}
            )

        self._sender.send_request(
            action='update_profile', user_data=user_data
        )


class AddContact(CommonMixin, QDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sender = Sender(self.client)
        self.init_ui()

    def init_ui(self):

        titles = ('contact',)

        add_contact = FormFactory(fields=titles)
        add_contact.construct()

        add_contact_group = QGroupBox('Add contact')
        add_contact_group.setLayout(add_contact)

        add_button = QPushButton('Add')
        add_button.clicked.connect(self.send_add_contact_request)

        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.close)

        h_layout = QHBoxLayout()
        h_layout.addWidget(add_button)
        h_layout.addWidget(cancel_button)

        v_layout = QVBoxLayout()
        v_layout.addWidget(add_contact_group)
        v_layout.addLayout(h_layout)

        self.setLayout(v_layout)
        self.setWindowTitle('Add contact')
        self.setFixedSize(self.sizeHint())

    def send_add_contact_request(self):
        widgets = self.findChildren(TitledLineEdit)

        user_data = {
            widget.title: widget.text().strip()
            for widget in widgets
        }

        user_data.update(
            {'username': self.parent.username}
        )

        self._sender.send_request(action='add_contact', user_data=user_data)


class ChatWindow(CommonMixin, CenterMixin, QWidget):

    update_model_add = pyqtSignal(dict)
    update_model_delete = pyqtSignal(str)
    append_messages_to_textbox = pyqtSignal(list)
    append_message_to_textbox = pyqtSignal(dict)
    set_searched_messages = pyqtSignal(list)
    set_avatar_signal = pyqtSignal(str)
    open_chat = pyqtSignal(dict)
    open_profile = pyqtSignal(dict)

    active_chat: int
    messages_lenght: int

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sender = Sender(self.client)
        self.ftp_client = FtpClient()

        self.profile_listener = ProfileListener(self, self.client.notifier)
        self.contact_listener = ContactListener(self, self.client.notifier)
        self.chat_listener = ChatListener(self, self.client.notifier)
        self.avatar_listener = AvatarListener(self, self.client.notifier)
        self.new_message_listener = NewMessageListener(
            self, self.client.notifier
        )
        self.search_message_listener = SearchMessageListener(
            self, self.client.notifier
        )

        self.update_model_add.connect(self.update_contacts_list_add)
        self.update_model_delete.connect(self.update_contacts_list_delete)
        self.append_messages_to_textbox.connect(self.append_messages)
        self.append_message_to_textbox.connect(self.append_message)
        self.set_avatar_signal.connect(self.set_avatar)
        self.open_chat.connect(self.activate_chat)
        self.open_profile.connect(self.profile_dialog)
        self.set_searched_messages.connect(self.set_messages)

        self.add_contact_window = AddContact(client=self.client, parent=self)

        self.init_ui()
        self.chats_data = {}

    def __call__(self, kwargs):
        self.username = kwargs.get('user_data').get('username')
        self.user_label.setText(f'{self.username}')
        self.user_id = kwargs.get('user_data').get('user_id')
        self.contacts = kwargs.get('user_data').get('contacts')
        self.init_model(self.contacts.keys())
        self.column_view.setModel(self.model)
        self.show()

    def init_model(self, contacts):
        if hasattr(self, 'model'):
            self.model.setStringList(contacts)
        else:
            self.model = QStringListModel(contacts)

    def init_ui(self):

        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)

        self.user_label = QLabel()
        self.user_label.setFont(font)

        self.avatar_label = QLabel()
        self.avatar_label.setHidden(True)
        profile_button = QPushButton('Change profile')
        profile_button.setAutoDefault(False)
        profile_button.clicked.connect(self.send_profile_request)

        v_user_layout = QVBoxLayout()
        v_user_layout.addWidget(self.user_label)
        v_user_layout.addWidget(profile_button)

        h_user_layout = QHBoxLayout()
        h_user_layout.addWidget(self.avatar_label)
        h_user_layout.addLayout(v_user_layout)
        h_user_layout.setAlignment(Qt.AlignLeft)

        client_group = QGroupBox('Client')
        client_group.setLayout(h_user_layout)

        self.status_group = StatusGroup(
            'Status log', client=self.client
        )

        self.column_view = QColumnView()
        self.column_view.setFixedWidth(100)
        self.column_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.column_view.doubleClicked.connect(self.send_chat_request)

        lbl_contacts = QLabel('Contacts')

        btn_common_chat = QPushButton('Common chat')
        btn_common_chat.clicked.connect(self.send_common_chat_request)
        btn_common_chat.setAutoDefault(False)

        btn_add_contact = QPushButton('Add contact')
        btn_add_contact.clicked.connect(self.add_contact)
        btn_add_contact.setAutoDefault(False)

        btn_delete_contact = QPushButton('Delete contact')
        btn_delete_contact.clicked.connect(self.delete_contact)
        btn_delete_contact.setAutoDefault(False)

        v_contacts_layout = QVBoxLayout()
        v_contacts_layout.addWidget(lbl_contacts)
        v_contacts_layout.addWidget(self.column_view)
        v_contacts_layout.addWidget(btn_common_chat)
        v_contacts_layout.addWidget(btn_add_contact)
        v_contacts_layout.addWidget(btn_delete_contact)

        path = os.path.join(settings.BASE_DIR, 'media')

        self.search_message = QLineEdit()
        self.search_message.setPlaceholderText('Enter word to search')
        self.search_message.returnPressed.connect(self.search_in_chat)

        message_search = QAction(
            QIcon(os.path.join(path, 'search.png')), 'Search', self
        )
        message_search.triggered.connect(self.search_in_chat)

        search_message_toolbar = QToolBar('Search')
        search_message_toolbar.addAction(message_search)

        h_search_layout = QHBoxLayout()
        h_search_layout.addWidget(self.search_message)
        h_search_layout.addWidget(search_message_toolbar)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setDisabled(True)

        lbl_enter = QLabel('Enter message')
        self.message_line_edit = QLineEdit()
        self.message_line_edit.setDisabled(True)
        self.message_line_edit.setTextMargins(10, 0, 10, 0)
        self.message_line_edit.returnPressed.connect(self.send_message_request)

        bold = QAction(QIcon(os.path.join(path, 'b.jpg')), 'Bold', self)
        italic = QAction(
            QIcon(os.path.join(path, 'i.jpg')), 'Italic', self
        )
        underlined = QAction(
            QIcon(os.path.join(path, 'u.jpg')), 'Underlined', self
        )

        toolbar = QToolBar('Formatting')
        toolbar.addAction(bold)
        toolbar.addAction(italic)
        toolbar.addAction(underlined)

        bold.triggered.connect(self.action_bold)
        italic.triggered.connect(self.action_italic)
        underlined.triggered.connect(self.action_underlined)

        v_chat_layout = QVBoxLayout()
        # v_chat_layout.addWidget(toolbar)
        v_chat_layout.addLayout(h_search_layout)
        v_chat_layout.addWidget(self.chat_text_edit)
        v_chat_layout.addWidget(lbl_enter)
        v_chat_layout.addWidget(self.message_line_edit)

        h_box_layout = QHBoxLayout()
        h_box_layout.addLayout(v_contacts_layout)
        h_box_layout.addLayout(v_chat_layout)

        v_main_layout = QVBoxLayout()
        v_main_layout.addWidget(client_group)
        v_main_layout.addWidget(self.status_group)
        v_main_layout.addLayout(h_box_layout)

        self.setLayout(v_main_layout)
        self.setFixedSize(500, 700)
        self.setWindowTitle('Chat')
        self.to_center()

    def search_in_chat(self):
        word = self.search_message.text()

        user_data = {
            'username': self.username,
            'word': word,
            'chat_id': self.active_chat,
        }

        self._sender.send_request(action='search_in_chat', user_data=user_data)

    def set_messages(self, messages):
        if messages:
            self.chat_text_edit.clear()
            for message in messages:
                self.chat_text_edit.append(
                    '{}: {}'.format(message[0], message[1])
                )

    def action_bold(self):
        myFont = QFont()
        myFont.setBold(True)
        self.chat_text_edit.setFont(myFont)

    def action_italic(self):
        myFont = QFont()
        myFont.setItalic(True)
        self.chat_text_edit.setFont(myFont)

    def action_underlined(self):
        myFont = QFont()
        myFont.setUnderline(True)
        self.chat_text_edit.setFont(myFont)

    def set_avatar(self, path):
        avatar_thread = threading.Thread(target=self.fetch_ftp, args=(path,))
        avatar_thread.start()

    def fetch_ftp(self, path):
        self.ftp_client.connect()
        data = self.ftp_client.download_file(path)

        if data:
            pixmap = QPixmap()
            pixmap.loadFromData(data.getvalue())
            self.avatar_label.setPixmap(pixmap)
            self.avatar_label.setHidden(False)
        else:
            self.avatar_label.setText(
                'Error has occurred when downloading avatar'
            )

    def profile_dialog(self, data):
        data.update(
            {'username': self.username, 'client': self.parent.client}
        )
        self.profile_dialog = ProfileForm(**data)
        self.profile_dialog.show()

    def send_profile_request(self):
        self._sender.send_request(
            action='profile', user_data={'username': self.username}
        )

    def send_chat_request(self, item):
        user_data = {
            'user_id': self.user_id,
            'contact_id': self.contacts.get(item.data()),
            'username': self.username
        }
        self._sender.send_request(action='get_chat', user_data=user_data)

    def send_common_chat_request(self):
        self._sender.send_request(
            action='common_chat', user_data={'username': self.username}
        )

    def send_message_request(self):
        message = self.message_line_edit.text()

        user_data = {
            'username': self.username,
            'message': message,
            'chat_id': self.active_chat,
            'user_id': self.user_id,
            'contact_user_id': self.chats_data.get(self.active_chat).get(
                'contact_user_id'),
            'contact_username': self.chats_data.get(self.active_chat).get(
                'contact_username')
        }

        self._sender.send_request(action='add_message', user_data=user_data)
        self.message_line_edit.clear()

    def append_messages(self, messages):
        if messages:
            for message in messages:
                self.chat_text_edit.append(
                    '{0}: {1}'.format(message[0], message[1])
                )

    def append_message(self, message):
        self.chat_text_edit.append(
                    '{0}: {1}'.format(message.get('sender'), message.get('text'))
                )

    def add_contact(self):
        self.add_contact_window.show()

    def delete_contact(self):
        contact = self.column_view.currentIndex().data()
        contact_id = self.contacts.get(contact)

        user_data = {
            'username': self.username,
            'contact_id': contact_id,
            'contact': contact
        }

        self._sender.send_request(action='delete_contact', user_data=user_data)

    def update_contacts_list_add(self, contact: Dict) -> None:
        self.contacts.update(contact)
        self.model.setStringList(self.contacts.keys())
        self.column_view.repaint()

    def update_contacts_list_delete(self, contact: str) -> None:
        self.contacts.pop(contact)
        self.model.setStringList(self.contacts.keys())
        self.column_view.repaint()

    def activate_chat(self, data):
        self.active_chat = data.get('chat_id')
        self.messages_lenght = data.get('lenght')
        self.chat_text_edit.clear()

        self.chats_data.update(
            {
                self.active_chat: {
                    'contact_user_id': data.get('contact_user_id'),
                    'contact_username': data.get('contact_username')
                }
            }
        )

        self.chat_text_edit.setDisabled(False)
        self.message_line_edit.setDisabled(False)
        self.chat_text_edit.clear()

        messages = data.get('messages')

        if messages:
            self.append_messages_to_textbox.emit(messages)

    def closeEvent(self, event):
        self._sender.send_request(
            action='logout', user_data={'username': self.username}
        )

        event.accept()
        self.parent.show()

        self.chat_text_edit.clear()
        self.chat_text_edit.setDisabled(True)
        self.message_line_edit.setDisabled(True)


class ClientGui(CenterMixin, QWidget):
    """Client application base window"""

    client = Client()
    chat = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()

        self.register_window = RegistrationForm(
            client=self.client, parent=self
        )
        self.login_window = LoginForm(client=self.client, parent=self)
        self.settings_window = SettingsForm(client=self.client, parent=self)
        self.chat_window = ChatWindow(client=self.client, parent=self)
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

        self.register_window.show()
        self.setVisible(False)

    def login_dialog(self):
        """Opens login dialog form"""

        self.login_window.show()
        self.setVisible(False)

    def settings_dialog(self):
        """Opens settings dialog form"""

        self.settings_window.show()
        self.setVisible(False)

    def chat_window(self, response):
        """Opens chat window"""
        self.chat_window(response)
        self.setVisible(False)


if __name__ == '__main__':
    app = QApplication([])
    widget = ChatWindow()
    sys.exit(app.exec_())
