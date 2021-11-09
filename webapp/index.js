
// Node Standard Library imports
const http = require('http');
const path = require('path');


// 3rd Party Library imports
const express = require('express');
const socketIO = require("socket.io");
const redis = require("redis");
const expressSession = require('express-session');
const redisStore = require('connect-redis')(expressSession);
const { loginWithCodeController } = require("./controllers/login");

// Webapp imports
const { handleSocketConnection } = require("./socket_handler");
const { get_rooms } = require("./lib/db/get_rooms");
const locals = require("./applocals")


// Setup server
const port = 8000;
const expressApp = express();
const httpServer = http.createServer(expressApp);
const io = new socketIO.Server(httpServer);

// Register static asset directories
expressApp.use('/static', express.static('static'));

// JSON Parsing for HTTP requests.
expressApp.use(express.json())

// Setup session
const redisClient  = redis.createClient();
expressApp.use(expressSession({
    secret: locals.sessionKey,
    store: new redisStore({
        host: 'localhost',
        port: 6379,
        client: redisClient,
        ttl: 260
    }),
    saveUninitialized: false,
    resave: false,
    cookie: { secure: locals.sessionCookieSecureOnly }
}));


io.on('connection', (socket) => handleSocketConnection(io, socket));


// Register HTTP Routes

expressApp.get('/', (req, res) => {
    /* Landing Page
    */
    if (!req.session.player_id) {
        return res.sendFile(path.join(__dirname, 'templates/login_with_code.html'));
    }

    if(!req.session.room_id) {
        return res.sendFile(path.join(__dirname, 'templates/join_room.html'));
    }

    res.send("<h1>Hello " + req.session.player_id + "</h1>")
});

expressApp.post('/loginwithcode', loginWithCodeController);
expressApp.get('/logout', (req, res) => {
    req.session.destroy();
    return res.redirect('/');
});

expressApp.get('/rooms', (req, res) => {
    const rooms = await get_rooms();
    return res.status(200).json(rooms);
});


// Launch the HTTP Server
httpServer.listen(port, () => {
    console.log('listening on *:' + port);
});
