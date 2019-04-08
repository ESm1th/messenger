import json
import time


def presence_parser(msg):
    message = json.loads(msg)
    user = message.get('user').get('account_name')
    action = message.get('action')
    if action == 'presence':
        response_message = {
            'response': 200,
            'time': time.time(),
            'alert': f'Hello { user }!'
        }
    else:
        response_message = {
            'response': 400,
            'time': time.time(),
            'error': 'Server waiting "presence" message'
        }
    return json.dumps(response_message)
