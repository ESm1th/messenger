from datetime import datetime
from routes import get_server_routes
from protocol import (
    validate_request, make_response,
    make_400, make_404
)


request = {
    'action': 'echo',
    'time': datetime.now(),
    'data': 'Testing string'
}


def test_validate_request():
    boolean_value = validate_request(request)
    assert boolean_value is True


def test_make_response():
    response = make_response(request, 200)
    assert response.get('action') == request.get('action')
    assert response.get('data') is None


def test_make_400():
    request.pop('action')
    response = make_400(request)
    assert response.get('action') is None


def test_make_404():
    actions = (
        route['action'] for route in get_server_routes()
    )
    request['action'] = 'not supported'
    response = make_404(request)

    assert response.get('action') not in actions
