import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ENCODING_NAME = 'utf-8'
BUFFER_SIZE = 65536
HOST = 'localhost'
PORT = 40000
CONNECTIONS = 7

INSTALLED_MODULES = [
    'auth',
    'chat'
]

with open(os.path.join(BASE_DIR, 'credentials.json')) as file:
    MONGO_CREDENTIALS = json.load(file)

SALT = '0dbdf63b1f2c0a465b7638e0fec73c66e6a51f62f170545ac6a6d7e177d91945'
