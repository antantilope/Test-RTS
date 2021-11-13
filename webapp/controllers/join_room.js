

const net = require('net');

const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_user_details } = require("../lib/db/get_user_details");
const { get_room_and_player_details, get_room } = require("../lib/db/get_rooms");
const { mint_team_uuid } = require("../lib/db/mint_team_uuid");
const { get_rooms_page_name, get_room_room_name } = require("../lib/room_names");
const {
    EVENT_ROOM_LIST_UPDATE,
    EVENT_LOBBY_UPDATE,
    EVENT_PUBMSG
} = require("../lib/event_names");
const {
    PHASE_0_LOBBY,
} = require("../constants");
const { logger } = require("../lib/logger");


const addPlayerToRoom = async (db, player_uuid, room_uuid, team_uuid) => {
    const sql1 = `
        INSERT INTO api_team
        (uuid, room_id, is_observer)
        VALUES (?, ?, ?)
    `;
    const sql2 = `
        UPDATE api_player SET team_id = ? WHERE uuid = ?
    `;
    return Promise.all([
        db.run(sql1, [team_uuid, room_uuid, false]),
        db.run(sql2, [team_uuid, player_uuid]),
    ]);
}


exports.joinRoomController = async (req, res) => {
    const room_uuid = req.body.room_uuid;
    if (!room_uuid) {
        return res.status(400).send("room_uuid is required")
    }

    const sess_player_id = req.session.player_id
    const sess_room_id = req.session.room_id
    const sess_team_id = req.session.team_id

    // Validate session data
    if (!sess_player_id) {
        return res.sendStatus(401);
    }
    if (sess_room_id || sess_team_id) {
        return res.status(400).send(
            "(SESS) player is already a room/team member room " + sess_room_id + ", team " + sess_team_id
        );
    }


    logger.info("Adding player too room, saving changes to database...")

    const db = await get_db_connection();
    try {
        // Validate database data
        const userDetails = await get_user_details(db, sess_player_id);
        if (typeof userDetails === 'undefined') {
            logger.error("Unable To Find User " + sess_player_id);
            return res.status(500).send("Could not find user with id " + sess_player_id)
        }

        if(userDetails.team_uuid || userDetails.room_uuid) {
            return res.status(400).send(
                "(DB) player is already a room/team member room " + userDetails.room_uuid + ", team " + userDetails.team_uuid
            );
        }

        let room = await get_room_and_player_details(db, room_uuid);
        let port = room.roomDetails.port;
        if (typeof room.roomDetails === 'undefined') {
            logger.error("Unable To Find Room to Join " + room_uuid);
            return res.status(500).send("Could not find room with id " + room_uuid)
        }

        if(room.roomDetails.player_count >= room.roomDetails.max_players) {
            return res.status(400).send("Room is full.");
        }
        if(room.roomDetails.phase !== PHASE_0_LOBBY) {
            return res.status(400).send("Cannot join room.");
        }

        // Write changes to database.
        const team_uuid = await mint_team_uuid(db);
        const resp = await addPlayerToRoom(db, sess_player_id, room_uuid, team_uuid);

        if (resp.length === resp.filter(r => r.changes === 1).length) {

            logger.silly("Changes saved to database");

            // Refresh room data.
            room = await get_room_and_player_details(db, room_uuid);
            delete room.roomDetails.port;
            room.userIsOwner = room.roomDetails.room_owner === req.session.player_id

            // Write changes to session.
            logger.silly("updating session");
            req.session.room_id = room_uuid;
            req.session.team_id = team_uuid;

            // Emit socket event to rooms list page.
            logger.silly("emitting room list update event");
            req.app.get('socketio')
                .to(get_rooms_page_name())
                .emit(
                    EVENT_ROOM_LIST_UPDATE,
                    {
                        uuid: room.roomDetails.uuid,
                        name: room.roomDetails.name,
                        max_players: room.roomDetails.max_players,
                        player_count: room.roomDetails.player_count,
                        phase: PHASE_0_LOBBY,
                    },
                );

            // Emit socket event to room that was joined
            logger.silly("emitting lobby update event");
            req.app.get('socketio')
                .to(get_room_room_name(room.roomDetails.uuid))
                .emit(
                    EVENT_LOBBY_UPDATE,
                    room,
                    `🤖📢 ${userDetails.handle} has joined 👋`,
                );

            logger.info("Connecting to GameAPI port " + port);
            const client = new net.Socket();
            client.connect(port, 'localhost', () => {
                logger.info("connected to GameAPI");
                const dataToWrite = JSON.stringify({add_player:{player_name: userDetails.handle, player_id:userDetails.uuid}}) + "\n";
                logger.info("writing data to GameAPI " + dataToWrite);
                client.write(dataToWrite);
            });
            client.on("data", data => {
                logger.info("received add_player response from GameAPI, disconnecting...");
                client.destroy();
                let respData;
                try {
                    respData = JSON.parse(data);
                } catch(err) {
                    logger.error("expected JSON data, got", data);
                    throw err;
                }
                logger.silly(data)
                if(respData.ok) {
                    logger.info("emitting " + EVENT_PUBMSG + " event");
                    req.app.get('socketio')
                        .to(get_room_room_name(room.roomDetails.uuid))
                        .emit(
                            EVENT_PUBMSG,
                            `🤖✅ ${userDetails.handle} registered with game service`,
                        );
                }

            });

            return res.sendStatus(201);

        } else {
            logger.error("unexpected database response");
            logger.error(resp);
            return res.status(500).send(
                "Unable to save all changes."
            );
        }
    }
    catch(err) {
        throw err;
    }
    finally {
        db.close();
    }
}
