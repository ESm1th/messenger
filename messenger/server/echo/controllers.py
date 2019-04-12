from protocol import make_response, make_400


def get_echo(request):
    data = request.get('data')

    if data:
        return make_response(
            request, 200, data=data
        )

    return make_400(request)
