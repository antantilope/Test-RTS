
const net = require('net');

const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room_and_player_details } = require("../lib/db/get_rooms");
const { get_rooms_page_name, get_room_room_name } = require("../lib/room_names");
const { get_user_details } = require("../lib/db/get_user_details");
const { PHASE_1_STARTING, PHASE_2_LIVE } = require("../constants");
const { EVENT_STARTGAME, EVENT_ROOM_LIST_UPDATE  } = require("../lib/event_names");
const { logger } = require("../lib/logger");



const runGameLoop = (port, room_id) => {
    // TODO: query command queue
    // TODO: research KeepAlive for TCP sockets.
    const client = new net.Socket();
    client.connect(port, 'localhost', () => {
        logger.info("connected to GameAPI on port " + port);
        const payload = '{"run_frame":{"commands":[]}}\n';
        logger.info("writing data to GameAPI: " + payload);
        client.write(payload);
    });
    client.on("data", data => {
        logger.info("received response from GameAPI, disconnecting...");
        client.destroy();
        let respData;
        try {
            respData = JSON.parse(data);
        } catch(err) {
            logger.error("expected JSON data, got: " + data);
            logger.error(err);
            logger.error(data);
            throw err;
        }
        logger.silly(data);

        if (respData.phase == PHASE_2_LIVE) {
            setTimeout(() => {
                runGameLoop(port, room_id);
            });
        } else {
            logger.info("game phase is " + respData.phase);
        }
    });
}


const doCountdown = (room_id, req, port) => {
    const client = new net.Socket();
    logger.info('connecting to GameAPI on port ' + port)
    client.connect(port, 'localhost', () => {
        logger.info("connected to GameAPI");
        const dataToWrite = JSON.stringify({decr_phase_1_starting_countdown:{}}) + "\n";
        logger.info("writing data to GameAPI: " + dataToWrite);
        client.write(dataToWrite);
    });

    client.on("data", data => {
        logger.info("received decr_phase_1_starting_countdown response from GameAPI, disconnecting...");
        client.destroy();

        let respData;
        try {
            respData = JSON.parse(data);
        } catch(err) {
            logger.error("expected JSON data, got");
            logger.error(err);
            logger.error(data)
            throw err;
        }
        logger.silly(data);

        if(respData.ok && respData.phase === PHASE_1_STARTING)
        {
            logger.info("Count down: " + respData.game_start_countdown);
            logger.info("emitting " + EVENT_STARTGAME + " event");
            req.app.get("socketio")
                .to(get_room_room_name(room_id))
                .emit(
                    EVENT_STARTGAME,
                    {game_start_countdown: respData.game_start_countdown},
                );
            if(respData.game_start_countdown - 1 >= 0) {
                logger.info("scheduling next " + EVENT_STARTGAME + " event");
                setTimeout(()=>{
                    doCountdown(room_id, req, port);
                }, 1000);
            }
        }
        else if (respData.ok && respData.phase === PHASE_2_LIVE)
        {
            logger.info("Count down: 0");
            logger.info("emitting final " + EVENT_STARTGAME + " event")
            req.app.get("socketio")
                .to(get_room_room_name(room_id))
                .emit(
                    EVENT_STARTGAME,
                    {game_start_countdown: 0},
                );

            setTimeout(() => {
                runGameLoop(port, room_id);
            });
        }
    });
}


exports.startGameController = startGameController = async (req, res) => {
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

    logger.info("starting game, writing changes to database")

    const db = await get_db_connection();
    let playerDetails;
    let room;
    try {
        room = await get_room_and_player_details(db, sess_room_id);
        playerDetails = await get_user_details(db, sess_player_id);
        if(room.roomDetails.room_owner !== sess_player_id) {
            return res.status(400).send("user is not room owner");
        }
        if(room.players.length < 2) {
            return res.status(400).send("not enough players in the room");
        }

        logger.silly("Updating DB, setting phase = " + PHASE_1_STARTING);
        await db.run(
            'UPDATE api_room SET phase = ? WHERE uuid = ?',
            [PHASE_1_STARTING, room.roomDetails.uuid],
        );
    } catch(err) {
        throw err
    } finally {
        db.close()
    }

    // Return HTTP response.
    res.sendStatus(202);

    // Emit socket event to rooms list page.
    logger.info("emitting event to rooms list page");
    req.app.get('socketio')
        .to(get_rooms_page_name())
        .emit(
            EVENT_ROOM_LIST_UPDATE,
            {
                uuid: room.roomDetails.uuid,
                name: room.roomDetails.name,
                max_players: room.roomDetails.max_players,
                player_count: room.roomDetails.player_count,
                phase: PHASE_1_STARTING,
            },
        );


    // Update GameAPI to advance phase to "starting"
    logger.info("Connecting to GameAPI port " + room.roomDetails.port);
    const client = new net.Socket();
    client.connect(room.roomDetails.port, 'localhost', () => {
        logger.info("connected to GameAPI");
        const dataToWrite = JSON.stringify({advance_to_phase_1_starting:{}}) + "\n";
        logger.info("writing data to GameAPI " + dataToWrite);
        client.write(dataToWrite);
    });

    client.on("data", data => {
        logger.info("received advance_to_phase_1_starting response from GameAPI, disconnecting...");
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

        if(respData.ok && respData.phase === PHASE_1_STARTING) {
            logger.info("emitting " + EVENT_STARTGAME + " event");
            req.app.get('socketio')
                .to(get_room_room_name(sess_room_id))
                .emit(
                    EVENT_STARTGAME,
                    {game_start_countdown: respData.game_start_countdown},
                );

            logger.info("scheduling next countdown");
            setTimeout(()=>{
                doCountdown(sess_room_id, req, room.roomDetails.port);
            }, 1000);
        }
    });
}
