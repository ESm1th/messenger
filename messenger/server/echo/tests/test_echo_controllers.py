from echo.controllers import get_echo


def test_get_echo_200():
    data = 'Testing string'

    request = {
        'action': 'echo',
        'data': data
    }

    response = get_echo(request)
    assert response.get('code') == 200


def test_get_echo_400():
    request = {
        'action': 'echo'
    }

    response = get_echo(request)
    assert response.get('code') == 400


def test_get_echo_data():
    data = 'Testing string'

    request = {
        'action': 'echo',
        'data': data
    }

    response = get_echo(request)
    assert response.get('data') == data
