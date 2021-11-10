
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_user_count_on_team } = require("../lib/db/get_user_count_on_team")



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
    const sess_room_id = req.session.player_id;
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
    try {
        const playerCount = await get_user_count_on_team(db, sess_team_id);
        const deleteTeam = playerCount === 1;
        await removePlayerFromRoom(db, sess_player_id, sess_team_id, deleteTeam);
    } catch(err) {
        throw err
    } finally {
        db.close()
    }

    // Update Session
    delete req.session.room_id;
    delete req.session.team_id;


    return res.sendStatus(204);


}
