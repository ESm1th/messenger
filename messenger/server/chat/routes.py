from .controllers import (
    AddContact,
    DeleteContact,
    GetChat,
    AddMessage,
    Profile,
    UpdateProfile,
    SearchInChat,
    CommonChat
)


routes = [
    {'action': 'add_contact', 'controller': AddContact},
    {'action': 'delete_contact', 'controller': DeleteContact},
    {'action': 'get_chat', 'controller': GetChat},
    {'action': 'add_message', 'controller': AddMessage},
    {'action': 'profile', 'controller': Profile},
    {'action': 'update_profile', 'controller': UpdateProfile},
    {'action': 'search_in_chat', 'controller': SearchInChat},
    {'action': 'common_chat', 'controller': CommonChat}
]
