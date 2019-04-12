from datetime import datetime


def validate_request(request):
    request_time = request.get('time')
    request_action = request.get('action')

    if request_time and request_action:
        return True

    return False


def make_response(request, code, data=None):
    return {
        'action': request.get('action'),
        'user': request.get('user'),
        'time': datetime.now().timestamp(),
        'data': data,
        'code': code
    }


def make_400(request):
    return make_response(request, 400, 'Wrong request format')


def make_404(request):
    return make_response(request, 404, 'Action is not supported')
