
const net = require('net');

const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_user_details } = require("../lib/db/get_user_details");
const { get_room_room_name } = require("../lib/room_names");
const { get_room } = require("../lib/db/get_rooms");
const { PHASE_0_LOBBY } = require("../constants")
const { EVENT_MAPCONFIG } = require("../lib/event_names");
const { logger } = require("../lib/logger");


exports.configureMapController = async (req, res) => {
    const sess_player_id = req.session.player_id;
    const sess_room_id = req.session.room_id;
    const sess_team_id = req.session.team_id;

    // Validate session data
    if (!sess_player_id) {
        return res.sendStatus(401);
    }
    if(!sess_room_id || !sess_team_id) {
        return res.status(400).send("invalid session");
    }

    // Validate request body
    const units_per_meter = 10;
    const x_unit_length = parseInt(req.body.x_unit_length);
    const y_unit_length = parseInt(req.body.y_unit_length);
    if (isNaN(units_per_meter) || isNaN(x_unit_length) || isNaN(y_unit_length)) {
        return res.status(400).send("invalid x_unit_length, y_unit_length")
    }
    if (units_per_meter < 5 || x_unit_length < 10000 || y_unit_length < 10000) {
        return res.status(400).send("invalid x_unit_length, y_unit_length, must be > 10000")
    }

    logger.silly("Configuring map, saving changes to database...");
    const db = await get_db_connection();
    let userDetails;
    let room;
    try {
        // Validate database data
        userDetails = await get_user_details(db, sess_player_id);
        if (typeof userDetails === 'undefined') {
            console.error("Unable To Find User");
            return res.status(500).send("Could not find user with id " + sess_player_id)
        }
        room = await get_room(db, sess_room_id);
        if (typeof room === 'undefined') {
            console.error("Unable To Find room");
            return res.status(500).send("Could not find room with id " + sess_room_id)
        }

        if(room.room_owner !== sess_player_id) {
            return res.status(403).send("Only the room owner can configure the map.")
        }
        if(room.phase !== PHASE_0_LOBBY) {
            return res.status(400).send("room phase must be lobby to configure map, phase is " + room.phase);
        }
    }
    catch (err) {
        throw err;
    }
    finally {
        db.close();
    }

    logger.silly("Changes saved to database, updating GameAPI...");
    res.sendStatus(202);

    logger.info("Connecting to GameAPI port " + room.port)
    const client = new net.Socket();
    client.connect(room.port, 'localhost', () => {
        logger.info("connected to GameAPI");
        const dataToWrite = `{"configure_map":{"units_per_meter":${units_per_meter}, "x_unit_length":${x_unit_length}, "y_unit_length":${y_unit_length}}}\n`
        logger.info("writing data to GameAPI" + dataToWrite);
        client.write(dataToWrite);
    });
    client.on("data", data => {
        logger.info("received configure configure_map from GameAPI, disconnecting...")
        client.destroy();
        let respData;
        try {
            respData = JSON.parse(data);
        } catch(err) {
            console.error("expected JSON data, got", data);
            throw err;
        }
        logger.silly(data);
        if(respData.ok) {
            logger.info("emitting " + EVENT_MAPCONFIG + " event");
            req.app.get('socketio')
                .to(get_room_room_name(room.uuid))
                .emit(
                    EVENT_MAPCONFIG,
                    {
                        x_km: Math.floor(respData.map_config.x_unit_length / (respData.map_config.units_per_meter * 1000)),
                        y_km: Math.floor(respData.map_config.y_unit_length / (respData.map_config.units_per_meter * 1000)),
                    }
                );
        }
    });

}
