import pytest
from datetime import datetime
from routes import get_server_routes

# fixtures for all tests in project
# all fixtures automatically loads for all test modules


@pytest.fixture(scope='module')
def valid_request():
    return {
        'action': 'echo',
        'time': datetime.now().timestamp(),
        'data': 'Test string'
    }


@pytest.fixture(scope='module')
def invalid_request():
    return {}


@pytest.fixture(scope='module')
def invalid_action_request():
    return {
        'action': 'not supported',
        'time': datetime.now().timestamp()
    }


@pytest.fixture(scope='module')
def success_code():
    return 200


@pytest.fixture(scope='module')
def valid_response(success_code):
    return {
        'action': 'echo',
        'user': None,
        'time': datetime.now().timestamp(),
        'data': 'Test string',
        'code': success_code
    }


@pytest.fixture(scope='module')
def controller():
    return lambda arg: print(arg)


@pytest.fixture(scope='module')
def routes(controller):
    return [
        {'action': 'echo', 'controller': controller}
    ]


@pytest.fixture(scope='module')
def actions():
    return (
        route.get('action') for route in get_server_routes()
    )
