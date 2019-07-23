# Messenger 
Simple client and server realisation of instant messenging application.

### Features
- instant messaging
- user handling (registration, authentication)
- one to one chat
- common chat
- adding and deleting contacts
- messages are stored on server in **mongodb**
- password are stored as hash
- ftp server used to store, load and fetch images (avatars)
- logging with **logging** module
- server is working asynchronously

### Folder structure
```
+---messenger
      |   requirements.txt
      +---client
      |   |   core.py
      |   |   gui.py
      |   |   observers.py
      |   |   settings.py
      |   |   __init__.py
      |   |   __main__.py
      |   +---media
      |           
      +---server
          |   core.py
          |   gui.py
          |   mongo.py
          |   observers.py
          |   settings.py
          |   __init__.py
          |   __main__.py
          |   
          +---auth
          +---chat
          +---media
          +---tests
```
### How to start
Clone repository.

Create virtual environment and activate it:
```
virtualenv --python=python3.7 chat_env
source chat_env/bin/activate
```
Change directory to **messenger** and install dependencies:
```
pip install -r requirements.txt
```
To start **server** without GUI enter command from **messenger** folder:
```
python server
```
or from **messenger/server** folder:
```
python __main__.py
```
#### Optional parameters
| Option | Description |
|---|---|
|`-a, --address`|run with specific host ip|
|`-p, --port`|run with specific port number|
|`-g, --gui`|run with GUI if used, if not used run without GUI|

Run **server** with specific host address, port and GUI:
```
python server -a 127.0.0.1 -p 8001 -g
```

#### How it works
All interaction between client and server bases on requesr and response format.
Every proper request must contain action field. `Raw` request represented as json string.
##### Authentication request example:
```python
{
      "action": "login",
      "time": 1561018237.341436,
      "data": {
            "username": "test",
            "password": "test"
      }
}
```
Server application uses **MVC** architecture pattern.
Server creates `Request` object from json string and if it valid sends it to `Router` object which finds appropriate 'callback' class.
The result of class work is `Response` object, that sends to client.
##### Authentication response example:
```python
{
      "action": "login",
      "time": 1561018242.351142,
      "code": 200,
      "info": "Client logged in",
      "username": "test",
      "user_id": 1,
      "contacts": {}
}
```
