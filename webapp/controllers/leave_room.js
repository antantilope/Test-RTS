
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_team_details } = require("../lib/db/get_team_details")
const { get_rooms_page_name } = require("../lib/room_names");
const { get_room } = require("../lib/db/get_rooms");
const { EVENT_ROOM_LIST_UPDATE } = require("../lib/event_names");
const {
    PHASE_0_LOBBY,
} = require("../constants");


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


exports.leaveRoomController = async (req, res) => {
    const sess_player_id = req.session.player_id;
    const sess_room_id = req.session.room_id;
    const sess_team_id = req.session.team_id;

    if (!sess_player_id) {
        return res.sendStatus(403);
    }
    if (!sess_room_id && !sess_team_id) {
        return res.status(400).send("session does not contain room_id or team_id");
    }
    if (!sess_room_id || !sess_team_id) {
        return res.status(500).send("invalid session");
    }

    // Update database
    const db = await get_db_connection();
    let roomDetails;
    try {
        roomDetails = await get_room(db, sess_room_id);
        const teamDetails = await get_team_details(db, sess_team_id);
        const deleteTeam = teamDetails.player_count === 1;
        await removePlayerFromRoom(db, sess_player_id, sess_team_id, deleteTeam);
    } catch(err) {
        throw err
    } finally {
        db.close()
    }

    // Update Session
    delete req.session.room_id;
    delete req.session.team_id;

    // Emit socket event to rooms list page.
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

    return res.sendStatus(204);
}
