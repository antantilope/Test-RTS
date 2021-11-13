

const { logger } = require("./lib/logger");


const validateSessionHTTPMiddleware = (req, res, next) => {
    if (!req.session.player_id && (req.session.room_id || req.session.team_id)) {
        // No player ID, but room or session is filled in
        logger.warn("INVALID SESSION");
        logger.warn(JSON.stringify(req.session));
        res.status(500).send("invalid session. player id is not populated but room_id and/or team_id is populated.");
    }
    else if ((!req.session.room_id && req.session.team_id) || (req.session.room_id && !req.session.team_id)) {
        // room is set but team is not, or team is set and room is not
        logger.warn("INVALID SESSION");
        logger.warn(JSON.stringify(req.session));
        res.status(500).send("invalid session. room_id and team_id must both be populated, or neither can be populated.");
    }
    else {
        // Session is valid.
        next();
    }
}


const abbrId = (uuid) => {
    return Boolean(uuid) ? uuid.slice(0, 7) : ''
}

const requestLoggingMiddleware = (req, res, next) => {
    const sessionString = `SESS(player_id:${abbrId(req.session.player_id)} team_id:${abbrId(req.session.team_id)} room_id:${abbrId(req.session.room_id)})`;
    const currDate = new Date();
    const timeString = `${currDate.getHours()}:${currDate.getMinutes()}:${currDate.getSeconds()}`
    res.on('finish', ()=>{
        logger.http(`(${res.statusCode}) ${req.method} ${req.url} ${sessionString}`);
    });
    next();
}


exports.validateSessionHTTPMiddleware = validateSessionHTTPMiddleware;
exports.requestLoggingMiddleware = requestLoggingMiddleware
