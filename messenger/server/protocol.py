from datetime import datetime
from routes import get_routes_map
from decorators import logged


@logged
def validate_request(request):
    request_time = request.get('time')
    request_action = request.get('action')

    if request_time and request_action:
        return True

    return False


@logged
def validate_action(request):
    if request.get('action') in get_routes_map():
        return True

    return False


@logged
def make_response(request, code, data=None):
    return {
        'action': request.get('action'),
        'user': request.get('user'),
        'time': datetime.now().timestamp(),
        'data': data,
        'code': code
    }


@logged
def make_400(request):
    return make_response(request, 400, 'Wrong request format')


@logged
def make_404(request):
    return make_response(request, 404, 'Action is not supported')
