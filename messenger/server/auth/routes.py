from .controllers import (
    Register,
    Login,
    Logout
)

routes = [
    {'action': 'register', 'controller': Register},
    {'action': 'login', 'controller': Login},
    {'action': 'logout', 'controller': Logout}
]
