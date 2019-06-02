from .controllers import (
    Contacts,
    AddContact,
    DeleteContact
)


routes = [
    {'action': 'get_contacts', 'controller': Contacts},
    {'action': 'add_contact', 'controller': AddContact},
    {'action': 'delete_contact', 'controller': DeleteContact}
]
