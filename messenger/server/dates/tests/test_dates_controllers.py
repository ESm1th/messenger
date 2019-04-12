from datetime import datetime
from dates.controllers import get_date_now


def test_get_date_now():
    date = datetime.now().strftime('%Y-%m-%d')

    request = {
        'action': 'now',
        'time': datetime.now().timestamp()
    }

    response = get_date_now(request)
    assert response.get('data') == date
