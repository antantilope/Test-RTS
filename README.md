# voidstar3

## Tech Stack

![VSTS (1)](https://user-images.githubusercontent.com/20848221/141389162-c5eafebc-eac0-47b1-a110-c0262ff9d8e4.jpg)

<hr>

## Installing Locally


### Python

Install python3.8.X from <a href="https://www.python.org" target="_blank">python.org</a>


### SQL Database setup
For now there is nothing that needs to be done here because django is configured to use sqlite.


### Setup a Python Virtual Environment and Install Packages
```bash
# from the project root run
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

exports.sessionKey = "secret key goes here"
exports.sessionCookieSecureOnly = false // for testing only

```


<hr>

## Start webserver & socket server

```bash
$ node index.js

# OR (npm i nodemon)
$ nodemon index.js
```

