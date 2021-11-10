
// Node Standard Library imports
const http = require('http');
const path = require('path');

// 3rd Party Library imports
const express = require('express');
const socketIO = require("socket.io");
const helmet = require('helmet');
const redis = require("redis");
const expressSession = require('express-session');
const redisStore = require('connect-redis')(expressSession);

// Webapp imports
const { loginWithCodeController } = require("./controllers/login");
const { joinRoomController } = require("./controllers/join_room");
const { leaveRoomController } = require("./controllers/leave_room")
const { handleSocketConnection } = require("./socket_handler");
const { get_db_connection } = require("./lib/db/get_db_connection");
const { get_rooms, get_room } = require("./lib/db/get_rooms");
const {
    validateSessionHTTPMiddleware,
    requestLoggingMiddleware,
} = require("./middleware");
const { PHASE_0_LOBBY } = require("./constants");
const locals = require("./applocals");



// Setup servers
const port = 8000;
const expressApp = express();
const httpServer = http.createServer(expressApp);
const io = new socketIO.Server(httpServer);

// Create session and bind as middleware.
const redisClient  = redis.createClient();
session = expressSession({
    secret: locals.sessionKey,
    store: new redisStore({
        host: 'localhost',
        port: 6379,
        client: redisClient,
        ttl: 260,
    }),
    rolling: true,
    saveUninitialized: false,
    resave: false,
    cookie: { secure: locals.sessionCookieSecureOnly },
})
io.use((socket, next) => {
    session(socket.request, socket.request.res || {}, next);
})
expressApp.use(session);

/* Register additional middleware.
*/
expressApp.use('/static', express.static('static'));
expressApp.use(express.json());
expressApp.use(requestLoggingMiddleware);
expressApp.use(validateSessionHTTPMiddleware);
expressApp.use(helmet({
    contentSecurityPolicy: false, // TODO: create a CSP. https://www.npmjs.com/package/helmet-csp
}));

/* Socket.IO connection handler.
*/
io.on('connection', (socket) => handleSocketConnection(io, socket));


/*
 *   Register HTTP Routes
 */
expressApp.get('/', async (req, res) => {
    /* Landing Page
    */

    // Player is not logged in
    if (!req.session.player_id) {
        return res.sendFile(path.join(__dirname, 'templates/login_with_code.html'));
    }

    // Player is logged in but not part of a room
    if(!req.session.room_id) {
        return res.sendFile(path.join(__dirname, 'templates/join_room.html'));
    }

    // Player is logged in and a room member.
    if(req.session.room_id && req.session.team_id) {
        let roomDetails;
        const db = await get_db_connection();
        try {
            roomDetails = await get_room(db, req.session.room_id);
        } catch (err) {
            throw err;
        } finally {
            db.close();
        }
        const roomInLobby = roomDetails.phase === PHASE_0_LOBBY;
        if (roomInLobby) {
            return res.sendFile(path.join(__dirname, 'templates/game_lobby.html'));
        } else {
            return res.send("<h1>GAME PAGE!</h1>")
        }

    }

    res.send("<h1>Hello " + req.session.player_id + "</h1>")
});

/* Log In, Log Out
*/
expressApp.post('/api/players/loginwithcode', loginWithCodeController);
expressApp.get('/logout', (req, res) => {
    req.session.destroy();
    return res.redirect('/');
});


/* Game Rooms
*/
expressApp.get('/api/rooms/list', async (req, res) => {
    const rooms = await get_rooms();
    for (let i in rooms) {
        delete rooms[i].port;
    }
    return res.status(200).json(rooms);
});

expressApp.post('/api/rooms/join', joinRoomController);
expressApp.post('/api/rooms/leave', leaveRoomController);


// Launch the HTTP Server
httpServer.listen(port, () => {
    console.log('listening on *:' + port);
});
