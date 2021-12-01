
// Node Standard Library imports
const http = require('http');
const path = require('path');

// 3rd Party Library imports
const express = require('express');
const socketIO = require("socket.io");
const helmet = require('helmet');
const csrf = require('csurf');
const cookieParser = require('cookie-parser');
const redis = require("redis");
const expressSession = require('express-session');
const redisStore = require('connect-redis')(expressSession);

// Webapp imports
const {
    loginWithCodeController,
    loginWithMagicLink,
} = require("./controllers/login");
const { joinRoomController } = require("./controllers/join_room");
const { leaveRoomController } = require("./controllers/leave_room");
const { roomDetailsController } = require("./controllers/room_details");
const { configureMapController } = require("./controllers/configure_map");
const {
    startGameController,
    relaunchGameLoops,
} = require("./controllers/start_game");
const {
    RunCommandController
} = require("./controllers/run_command");
const { userDetailsController } = require("./controllers/user_details");
const { pingServerController } = require("./controllers/ping_server");
const { handleSocketConnection } = require("./socket_handler");
const { get_db_connection } = require("./lib/db/get_db_connection");
const { get_rooms, get_room } = require("./lib/db/get_rooms");
const { get_user_details } = require("./lib/db/get_user_details");
const {
    validateSessionHTTPMiddleware,
    requestLoggingMiddleware,
} = require("./middleware");
const { PHASE_0_LOBBY } = require("./constants");
const { logger } = require("./lib/logger");
const locals = require("./applocals");


// Setup servers
const expressApp = express();
const httpServer = http.createServer(expressApp);
const io = new socketIO.Server(httpServer);

// Allow express app to access socket server from HTTP request context.
expressApp.set('socketio', io);

// Create session and bind as middleware.
expressApp.use(cookieParser())
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
});
expressApp.use(session);

/* Setup CSRF middleware
*/
const csrfProtection = csrf({ cookie: true });
expressApp.use(csrfProtection);
expressApp.use((req, res, next) => {
    res.cookie('csrftoken', req.csrfToken());
    next();
});

/* Register additional middleware.
*/
expressApp.use((req, res, next) => {
    if (/^\/static\/ng\/(index\.html)?$/.test(req.url)) {
        logger.warn("WARNING: Blocking direct access to /static/ng/index.html")
        res.sendStatus(404);
    } else {
        next();
    }
});
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
    res.setHeader('Content-Type', 'text/html; charset=UTF-8');

    if(req.session.player_id){
        // Player is logged in, Sync Session with SSOT
        const db = await get_db_connection();
        try {
            const playerDetails = await get_user_details(db, req.session.player_id);
            if(typeof playerDetails !== "undefined") {
                req.session.team_id = playerDetails.team_uuid;
                req.session.room_id = playerDetails.room_uuid;
            }
        } catch (err) {
            throw err;
        } finally {
            db.close();
        }
    }
    else {
        // Player is not logged in
        return res.sendFile(path.join(__dirname, 'templates/login_with_code.html'));
    }

    // Player is logged in but not part of a room
    if(!req.session.room_id) {
        return res.sendFile(path.join(__dirname, 'templates/join_room.html'));
    }

    // Player is logged in and a room member.
    if(req.session.room_id && req.session.team_id) {
        let roomDetails;
        let playerDetails;
        const db = await get_db_connection();
        try {
            roomDetails = await get_room(db, req.session.room_id);
            playerDetails = await get_user_details(db, req.session.player_id);
        } catch (err) {
            throw err;
        } finally {
            db.close();
        }

        if(!playerDetails.team_uuid) {
            // Session thinks player is in a room, but database does not have a team.
            // Clean up the session.
            logger.warn(
                "Session room/team info is mismatched with database. Deleting room/team IDs from session."
            );
            delete req.session.team_id;
            delete req.session.room_id;
            return res.sendFile(path.join(__dirname, 'templates/join_room.html'));
        }

        const roomInLobby = roomDetails.phase === PHASE_0_LOBBY;
        if (roomInLobby) {
            return res.sendFile(path.join(__dirname, 'templates/game_lobby.html'));
        } else {
            // Entry point to angular application.
            return res.sendFile(path.join(__dirname, 'static/ng/index.html'));
        }

    }

});

/* Log In, Log Out
*/
expressApp.post('/api/players/loginwithcode', loginWithCodeController);
expressApp.get('/loginwithlink', loginWithMagicLink);
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

expressApp.get('/api/users/details', userDetailsController);
expressApp.get('/api/rooms/ping', pingServerController);
expressApp.post('/api/rooms/join', joinRoomController);
expressApp.post('/api/rooms/leave', leaveRoomController);
expressApp.get('/api/rooms/details', roomDetailsController);
expressApp.post('/api/rooms/configure', configureMapController);
expressApp.post('/api/rooms/start', startGameController);
expressApp.post('/api/rooms/command', RunCommandController);

// Launch the HTTP Server
httpServer.listen(locals.port, () => {
    logger.info('listening on *:' + locals.port);
});


logger.info("Scheduling relaunchGameLoops")
setTimeout(() => {
    relaunchGameLoops(io, expressApp);
}, 3000);
