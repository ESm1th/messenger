import os
import json

DEFAULT_SETTINGS = True
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODING_NAME = 'utf-8'
BUFFER_SIZE = 65536
HOST = 'localhost'
PORT = 40000


try:
    with open(
        os.path.join(BASE_DIR, 'ftp.json')
    ) as file:
        data = json.load(file)

        FTP_HOST = data.get('host')
        FTP_USER = data.get('user')
        FTP_PASSWORD = data.get('password')
        FTP_PATH = data.get('path')

except Exception as error:
    print('File does not exists')
    raise error
