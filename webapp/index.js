
// Node Standard Library imports
const http = require('http');

// 3rd Party Library imports
const express = require('express');
const socketIO = require("socket.io");
const redis = require("redis");
const expressSession = require('express-session');
const redisStore = require('connect-redis')(expressSession);

// Webapp imports
const { handleSocketConnection } = require("./socket_handler");
const locals = require("./applocals")


// Setup server
const port = 8000;
const expressApp = express();
const httpServer = http.createServer(expressApp);
const io = new socketIO.Server(httpServer);

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
    console.log(req.session)
    req.session.aKey = 23;
    res.send('<h1>Hello world</h1>');
});


// Launch the HTTP Server
httpServer.listen(port, () => {
    console.log('listening on *:' + port);
});
