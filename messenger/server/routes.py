from importlib import import_module
from functools import reduce
from settings import INSTALLED_MODULES


def get_server_routes():
    """
    Return list of all routes from each module
    in INSTALLED_MODULES - [ {action: controller}, ... ]
    """
    return reduce(
        lambda routes, module: routes + getattr(
            import_module(f'{ module }.routes'), 'routes', []
        ),
        INSTALLED_MODULES,
        []
    )


def get_routes_map(routes=None):
    """
    Return dict with actions as keys and controllers as values from passed
    list of routes if it != None or from all server routes otherwise
    """
    return {
        route['action']: route['controller']
        for route in routes or get_server_routes()
    }


def resolve(action, routes=None):
    """
    Return controller for passed action if action exists in passed
    list of routes, if this list is not None, 
    or in all server routes, otherwise.
    Return None if passed action not exists in routes return None.
    """
    return get_routes_map(routes).get(action, None)


if __name__ == '__main__':
    routes = get_server_routes()
    now = resolve('now')
    echo = resolve('echo')
    message = resolve('message')
