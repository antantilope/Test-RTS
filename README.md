# Test RTS

This was an RTS I developed for several months and eventually abandoned. Now it serves as a codebase I ctrl+c/ctrl+v snippets from.

Useful pieces:
 - https://github.com/antantilope/Test-RTS/blob/main/api/utils2d.py
 - https://github.com/antantilope/Test-RTS/blob/main/webapp/appclient/src/app/drawing.service.ts#L1338

There are many problems with this app: the 2 main issues: UI/UX, netcode.

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
$ python3 -m venv env
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

### Create Example Maps
```
./webapp/appmodels/manage.py create_test_maps

```

### Run Game Python API Tests
```bash
./test_api
```

### API V2 C++ :ibraries

Download the following repos and add to include:
 - https://github.com/Tencent/rapidjson
 - https://github.com/gabime/spdlog

```bash
# you may need to tweak folder names these commands:

unzip rapidjson.zip
sudo cp -rv rapidjson/include/rapidjson /usr/local/include

unzip spdlog.zip
sudo cp -rv spdlog/include/spdlog /usr/local/include
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

exports.port = 8000
exports.host = 'localhost'
exports.sessionKey = "secret key goes here";
exports.sessionCookieSecureOnly = false; // for testing only

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
node scripts/create_user.js Derpson

# Get login links
node scripts/get_login_links.js
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
# From the webapp/ directory

$ ./devserver.sh
```

<hr>

## Cross Site Request Forgery (CSRF)
 - All responses from the express application will set a cookie called `csrftoken`
 - All unsafe requests to the express application (POST/PUT/PATCH/DELETE) must include the header `csrf-token`

```js
// Including token on Angular SPA.

// No extra work needs to be done. The http client is configured to include the token.
@NgModule({
  imports: [
    HttpClientXsrfModule.withOptions({
      cookieName: 'csrftoken',
      headerName: 'csrf-token',
    }),
  ]
})
export class AppModule { }
```

```js
// Including token on vanilla JS/JQuery page.

// Add this code to "ready" handler
$(document).ready(() => {

    window.csrftoken = (function (cname) {
        let name = cname + "=";
        let decodedCookie = decodeURIComponent(document.cookie);
        let ca = decodedCookie.split(';');
        for(let i = 0; i <ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) == ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) == 0) {
                return c.substring(name.length, c.length);
            }
        }
        return "";
    })("csrftoken");
    function csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("csrf-token", window.csrftoken);
            }
        }
    });

});

```
<hr>

## Codebase Tour

### Python Application (Game Logic)
 - api/
   - main.py
     - entry point for python application
     - defines syncronous socket server handler that communicates with nodejs middleware
     - calls game methods
   - constants.py
     - houses all constants used by the python application. Primarily holds ship properties.
   - models/
     - game.py
       - holds top level game logic and properties
       - holds ship level game logic that cannot run at the ship level or is inefficient to run at the ship level
       - calls ship methods
     - ship.py
       - holds ship level game logic and properties
     - ship_upgrades.py
       - defines ship upgrades and their costs, requirements, and effects
     - ship_designator.py
       - logic that assigns a random designator to each ship.
       - players do not see opponent's handle's. They only see this random designation.
    - utils2d.py
      - defines math intensive operations for managing objects on a 2-dimensional plane
        - trigonometry
        - geometry
        - physics
        - hitboxes
   - tests/
     - Holds unit tests for python application


### Node Backend Web Appliocation
 - webapp/
    - _index.js_ (entry point for express.js application)
    - _socket_handler.js_ define server side socket behavior for talking to the Angular app
    - appclient/ __(angular front end)__
    - static/
      - static files that are served by the web application
      - angular build files
    - appmodels/
      - this is a django project which only used for database migrations
    - scripts/
      - management commands
    - _controllers/_ express.js HTTP route handlers
      - _start_game.js_ handles server side socket behavior for talking to Python Game API. Maintains server tickrate using setTimeout
    - lib/
      - services for the express.js app
        - database client and methods
        - unix process managements
        - logging (winston)
        - event/socket/command namesspaces
    - templates/
      - HTML markup for non angular pages
