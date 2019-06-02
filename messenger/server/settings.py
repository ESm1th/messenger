import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODING_NAME = 'utf-8'
BUFFER_SIZE = 1024
HOST = 'localhost'
PORT = 8887
CONNECTIONS = 7

INSTALLED_MODULES = [
    'auth',
    'chat'
]
