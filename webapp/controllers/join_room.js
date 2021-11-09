
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_user_details } = require("../lib/db/get_user_details");
const { get_room } = require("../lib/db/get_rooms");
const { mint_team_uuid } = require("../lib/db/mint_team_uuid")

const {
    PHASE_0_LOBBY,
} = require("../constants");



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
        return res.sendStatus(403);
    }
    if (sess_room_id || sess_team_id) {
        return res.status(400).send(
            "(SESS) player is already a room/team member room " + sess_room_id + ", team " + sess_team_id
        );
    }

    const db = await get_db_connection();
    try {
        // Validate database data
        const userDetails = await get_user_details(db, sess_player_id);
        if (typeof userDetails === 'undefined') {
            console.error("Unable To Find User");
            return res.status(500).send("Could not find user with id " + sess_player_id)
        }

        if(userDetails.team_uuid || userDetails.room_uuid) {
            return res.status(400).send(
                "(DB) player is already a room/team member room " + userDetails.room_uuid + ", team " + userDetails.team_uuid
            );
        }

        const roomDetails = await get_room(db, room_uuid);
        if (typeof roomDetails === 'undefined') {
            console.error("Unable To Find Room to Join.");
            return res.status(500).send("Could not find room with id " + room_uuid)
        }

        if(roomDetails.player_count >= roomDetails.max_players) {
            return res.status(400).send("Room is full.");
        }
        if(roomDetails.phase !== PHASE_0_LOBBY) {
            return res.status(400).send("Cannot join room.");
        }

        // Write changes to database.
        const team_uuid = await mint_team_uuid(db);
        const resp = await addPlayerToRoom(db, sess_player_id, room_uuid, team_uuid);

        if (resp.length === resp.filter(r => r.changes === 1).length) {
            // Write changes to session.
            req.session.room_id = room_uuid;
            req.session.team_id = team_uuid;

            return res.sendStatus(201);

        } else {
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
