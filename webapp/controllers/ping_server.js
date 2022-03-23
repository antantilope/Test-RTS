
const net = require('net');

const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room } = require("../lib/db/get_rooms");
const { logger } = require("../lib/logger");


exports.pingServerController = async (req, res) => {
    const sess_player_id = req.session.player_id;
    const sess_room_id = req.session.room_id;
    const sess_team_id = req.session.team_id;

    if (!sess_player_id) {
        return res.sendStatus(401);
    }
    if (!sess_room_id && !sess_team_id) {
        return res.status(400).send("session does not contain room_id or team_id");
    }
    if (!sess_room_id || !sess_team_id) {
        return res.status(500).send("invalid session");
    }

    const db = await get_db_connection();
    let room;
    try {
        room = await get_room(db, sess_room_id);
        if(typeof room === 'undefined') {
            logger.error("Expected to find room with uuid but could not.")
            return res.sendStatus(500);
        }
    } catch(err) {
        throw err;
    } finally {
        db.close();
    }


    if(room.room_owner !== sess_player_id) {
        return res.sendStatus(403);
    }

    const port = room.port;
    logger.info("Connecting to GameAPI port " + port);
    const client = new net.Socket();
    client.on("error", (err) => {
        client.destroy();
        logger.error("PING controller could not connect to game server on port " + port);
        logger.error(JSON.stringify(err));
        return res.status(502).json(err);
    });
    client.connect(port, 'localhost', () => {
        logger.info("connected to GameAPI");
        const dataToWrite = JSON.stringify({ping:{}}) + "\n";
        logger.info("writing data to GameAPI " + dataToWrite);
        client.write(dataToWrite);
    });
    client.on("data", data => {
        logger.info("received ping response from GameAPI, disconnecting...");
        client.destroy();
        let respData;
        try {
            respData = JSON.parse(data);
        } catch(err) {
            logger.error("expected JSON data, got");
            logger.error(err);
            logger.error(data);
            throw err;
        }
        logger.silly(data);
        return res.json(respData);
    })

}
