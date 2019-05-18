from .controllers import (
    Register,
    Login
)

routes = [
    {'action': 'register', 'controller': Register},
    {'action': 'login', 'controller': Login}
]
