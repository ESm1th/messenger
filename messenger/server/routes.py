from importlib import import_module
from functools import reduce
from settings import INSTALLED_MODULES


def get_server_routes():
    return reduce(
        lambda routes, module: routes + getattr(
            import_module(f'{ module }.routes'), 'routes', []
        ),
        INSTALLED_MODULES,
        []
    )


def get_routes_map(routes=None):
    return {
        route['action']: route['controller']
        for route in routes or get_server_routes()
    }


def resolve(action, routes=None):
    return get_routes_map(routes).get(action, None)


if __name__ == '__main__':
    routes = get_server_routes()
    now = resolve('now')
    echo = resolve('echo')
    message = resolve('message')
