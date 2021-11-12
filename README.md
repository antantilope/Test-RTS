# voidstar3


![](https://media3.giphy.com/media/3FjEPbKqEPhPpmC8uY/giphy.gif?cid=ecf05e47mhdcyehw2x36vt8rt3rsohj4gf8f0d1dim455am2&rid=giphy.gif&ct=g)


<hr>

## Stack

![VSTS (1)](https://user-images.githubusercontent.com/20848221/141389162-c5eafebc-eac0-47b1-a110-c0262ff9d8e4.jpg)

<hr>

## Installing Locally


### Python

Install python3.8.X (or better) from <a href="https://www.python.org" target="_blank">python.org</a>


### SQL Database setup
For now there is nothing that needs to be done here because django is configured to use sqlite.


### Download Code
```bash
$ git clone git@github.com:stricoff92/voidstar3.git
$ cd voidstar3
```


### Setup a Python Virtual Environment and Install Packages
```bash
# from the project root rungit s
$ pip install virtualenv
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

### Add django locals file
```bash
$ touch webapp/appmodels/appmodels/applocals.py
```
```python
# Example applocals.py


# DO NOT COMMIT THIS FILE
SECRET_KEY = "secret key goes here"
```
To create secure keys:
```bash
$ python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Migrate SQL database
```
./webapp/appmodels/manage.py migrate

```

### Run Game Python API Tests
```bash
./test_api
```


### Node

Install at node 12 or better

```bash
$ cd webapp
$ npm install
```
### Add Node locals file
```bash
$ touch applocals.js
```
```node
// Example applocals.js


// DO NOT COMMIT THIS FILE

exports.sessionKey = "secret key goes here"
exports.sessionCookieSecureOnly = false // for testing only

```

### Install Redis.

<a href="https://redis.io/download">download page</a>
```bash
# start a server
$ redis-server

# Test with cli
$ redis-cli

127.0.0.1:6379> ping hello!

```


### Add users and a room

```bash
node scripts/create_superuser.js Jonst
node scripts/create_user.js leeHDrew

# Get player uuids
node scripts/print_users.js

node scripts/create_room.js USE_PLAYER_UUID_HERE "Test Room" 2 8001 0
node scripts/get_login_code.js USE_PLAYER_UUID_HERE
node scripts/get_login_code.js USE_PLAYER_UUID_HERE
```

### Install & Setup Angular

```bash
$ cd webapp/appclient
$ npm install

# if you hit dependancy conflict errors because of Jasmin/Karma
$ npm install --force

# Build dev assets and watch for changes
$ npm run-script builddev
```


<hr>

## Start webserver & socket server

```bash
$ node index.js

# OR (npm i nodemon)
$ nodemon index.js
```

<hr>

## How to contribute

```bash
# Create a branch
$ git checkout -b js_readme_update

# Make changes
$ vim README.md

$ git add .
$ git commit -m "added change to readme"
# First time pushing, afterwards you can just run "git push"
$ git push --set-upstream origin js_readme_update

$ git add .
$ git commit -m "more changes"
$ git push

$ git add .
$ git commit -m "more changes"
$ git push

# When you're done making changes, pdate feature branch with latest commits from master
$ git checkout main
$ git pull
$ git checkout js_readme_update
$ git merge main
$ git push
```

### Create a pull request

![Screenshot from 2021-11-12 09-37-32](https://user-images.githubusercontent.com/20848221/141484910-aacbdc3f-f9e4-47bd-acfb-591d00a3df46.png)

### Add comments describing changes

![Screenshot from 2021-11-12 09-39-32](https://user-images.githubusercontent.com/20848221/141484954-35dfd211-e6bf-4477-bdfa-8358a8103046.png)

### 🛑 🚨 DO NOT MERGE THE PR. I WILL DO IT 🚨 🛑

### After your branch is merged with main

```bash
$ git checkout main
$ git pull

# Delete branch
$ git branch -d js_readme_update
```


## Cross Site Request Forgery (CSRF)
 - All respondes from the express application will set a cookie called `csrftoken`
 - All unsafe requests to the express application (POST/PUT/PATCH/DELETE) must include the header `csrf-token`


