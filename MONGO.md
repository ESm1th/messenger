# mongo
Text below was written for OS:
```
Description:	Ubuntu 16.04.6 LTS
Codename:	xenial
```

### Installation
Copy public key from https://www.mongodb.org/static/pgp/server-4.0.asc
```
wget -qO - https://www.mongodb.org/static/pgp/server-4.0.asc | sudo apt-key add -
```
Create a list file for MongoDB
```
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
```
Reload local package database
```
sudo apt-get update
```
Install mongodb-org
```
sudo apt install -y mongodb-org
```
Check `mongo` version
```
mongo --version
```
