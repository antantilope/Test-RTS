
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room_and_player_details } = require("../lib/db/get_rooms");
const { PHASE_2_LIVE, PHASE_1_STARTING, PHASE_3_COMPLETE } = require("../constants")

exports.liveGameDetailsController = async (req, res) => {
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
    let room
    try {
        room = await get_room_and_player_details(db, sess_room_id);
    } catch(err) {
        throw err;
    } finally {
        db.close();
    }

    if (
        room.roomDetails.phase !== PHASE_2_LIVE
        && room.roomDetails.phase !== PHASE_1_STARTING
        && room.roomDetails.phase !== PHASE_3_COMPLETE
    ) {
        return res.sendStatus(400);
    }

    const playerIdToAssetName = {};
    for(let i in room.players) {
        playerIdToAssetName[
            room.players[i].player_uuid
        ] = room.players[i].ship_asset_name;
    }

    return res.status(200).json({
        playerIdToAssetName
    });
}
