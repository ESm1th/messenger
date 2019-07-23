# Messenger 
Simple client and server realisation of instant messenging application.

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

To start **server** with GUI enter command from **messenger** folder:
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
|`-a, --address`|set host ip|
|`-p, --port`|set port number|
|`-g, --gui`|run with GUI if used, if not used run without GUI|

Run **server** with specific host address, port and GUI:
```
python server -a 127.0.0.1 -p 8001 -g
```
