# MongoDB
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

### Enable access control
Connect to mongo
```
mongo
```

Create admin user in `admin` database
```javascript
use admin
db.createUser(
  {
    user: "admin",
    pwd: "password",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
  }
)
```

Change settings
```
sudo nano /etc/mongodb.conf
```

Uncomment `auth` string and save changes
```javascript
# Turn on/off security.  Off is currently the default
#noauth = true
auth = true
```

Restart mongo
```
sudo systemctl restart mongodb
```

Connect to `mongo` as `admin`
```
mongo admin -u admin -p
```

Create `client` user in `messenger` database
```javascript
use messenger
db.createUser(
  {
    user: "client",
    pwd: "password",
    roles: [ { role: "readWrite", db: "messenger" } ]
  }
)
```
**MongoDB** is set up now.
