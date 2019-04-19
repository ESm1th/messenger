from datetime import datetime
from protocol import make_response
from decorators import logged


@logged
def get_date_now(request):
    date = datetime.now()
    return make_response(
        request, 200, date.strftime('%Y-%m-%d')
    )
