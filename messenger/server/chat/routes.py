from .controllers import (
    Contacts,
    AddContact,
    DeleteContact,
    GetChat,
    AddMessage,
    NewMessageListener
)


routes = [
    {'action': 'get_contacts', 'controller': Contacts},
    {'action': 'add_contact', 'controller': AddContact},
    {'action': 'delete_contact', 'controller': DeleteContact},
    {'action': 'get_chat', 'controller': GetChat},
    {'action': 'add_message', 'controller': AddMessage},
    {'action': 'message_listener', 'controller': NewMessageListener}
]
