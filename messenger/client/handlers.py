import json
import time


def presence_message(username='Test', status='On board'):
    message = {
        'action': 'presence',
        'time': time.time(),
        'type': 'status',
        'user': {
            'account_name': username,
            'status': status
        }
    }
    return json.dumps(message)


def presence_response_parser(msg):
    message = json.loads(msg)
    response_code = message.get('response')

    if response_code == 200:
        response_message = message.get('alert')
        print(f'{ response_code } OK\n{ response_message }')
    elif response_code == 400:
        response_message = message.get('error')
        print(f'{ response_code } NOK\n{ response_message }')
