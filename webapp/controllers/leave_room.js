

const net = require('net');

const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_team_details } = require("../lib/db/get_team_details")
const { get_user_details } = require("../lib/db/get_user_details")
const { get_rooms_page_name, get_room_room_name } = require("../lib/room_names");
const { get_room, get_room_and_player_details } = require("../lib/db/get_rooms");
const {
    EVENT_ROOM_LIST_UPDATE,
    EVENT_LOBBY_UPDATE,
    EVENT_PUBMSG
} = require("../lib/event_names");
const {
    PHASE_0_LOBBY,
} = require("../constants");
const { logger } = require("../lib/logger");


const removePlayerFromRoom = async (db, player_uuid, team_uuid, deleteTeam) => {
    const sql1 = `
        UPDATE api_player SET team_id = NULL WHERE uuid = ?;
    `;
    const dbPromises = [
        db.run(sql1, [player_uuid])
    ];

    if (deleteTeam) {
        const sql2 = `
            DELETE FROM api_team WHERE uuid = ?;
        `;
        dbPromises.push(
            db.run(sql2, [team_uuid])
        );
    }

    return Promise.all(dbPromises);
}

exports.removePlayerFromRoom = removePlayerFromRoom;


exports.leaveRoomController = async (req, res) => {
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


    // Update database
    logger.info("Removing player from room, saving changes to database...");
    const db = await get_db_connection();
    let roomDetails;
    let updatedRoom;
    let playerDetails;
    try {
        roomDetails = await get_room(db, sess_room_id);
        if(!roomDetails) {
            return res.status(404).send("room not found");
        }
        if(roomDetails.phase != PHASE_0_LOBBY){
            return res.status(400).send("Cannot leave room in phase " + roomDetails.phase)
        }
        const teamDetails = await get_team_details(db, sess_team_id);
        const deleteTeam = teamDetails.player_count === 1;
        await removePlayerFromRoom(db, sess_player_id, sess_team_id, deleteTeam);
        updatedRoom = await get_room_and_player_details(db, sess_room_id);
        playerDetails = await get_user_details(db, sess_player_id);
    } catch(err) {
        throw err
    } finally {
        db.close()
    }
    logger.info("Changes saved to database");

    // Update Session
    logger.silly("updating session");
    delete req.session.room_id;
    delete req.session.team_id;

    // Emit socket event to rooms list page.
    logger.silly("emitting room list update event");
    req.app.get("socketio")
        .to(get_rooms_page_name())
        .emit(
            EVENT_ROOM_LIST_UPDATE,
            {
                uuid: roomDetails.uuid,
                name: roomDetails.name,
                max_players: roomDetails.max_players,
                player_count: roomDetails.player_count - 1,
                phase: PHASE_0_LOBBY,
            },
        )

    // Emit socket event to game lobby.
    logger.silly("emitting lobby update event");
    req.app.get("socketio")
        .to(get_room_room_name(sess_room_id))
        .emit(
            EVENT_LOBBY_UPDATE,
            updatedRoom,
            `🤖📢 ${playerDetails.handle} has left 👋`,
        );


    // Send
    logger.info("Connecting to GameAPI port " + roomDetails.port);
    const client = new net.Socket();
    client.connect(roomDetails.port, 'localhost', () => {
        logger.info("connected to GameAPI");
        const dataToWrite = JSON.stringify({remove_player:playerDetails.uuid}) + "\n";
        logger.info("writing data to GameAPI " + dataToWrite);
        client.write(dataToWrite);
    });
    client.on("data", data => {
        logger.info("received remove_player response from GameAPI, disconnecting...");
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
        if(respData.ok) {
            logger.info("emitting " + EVENT_PUBMSG + " event");
            req.app.get('socketio')
                .to(get_room_room_name(sess_room_id))
                .emit(
                    EVENT_PUBMSG,
                    `🤖✅ ${playerDetails.handle} unregistered with game service`,
                );
        }

    });


    return res.sendStatus(204);
}
