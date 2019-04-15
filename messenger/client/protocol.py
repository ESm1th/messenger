from datetime import datetime


def make_request(action, data=None, user=None):
    return {
        'action': action,
        'time': datetime.now().timestamp(),
        'user': user,
        'data': data
    }
