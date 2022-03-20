
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room_and_player_details } = require("../lib/db/get_rooms");
const { get_map_details } = require ("../lib/db/get_maps");
const { logger } = require("../lib/logger");

exports.roomDetailsController = async (req, res) => {
    if(!req.session.player_id) {
        return res.sendStatus(401);
    }

    const roomUUID = req.session.room_id
    if(!roomUUID) {
        return res.status(400).send("User not in room.");
    }

    const db = await get_db_connection();
    let roomDetailsAndPlayers;
    try {
        roomDetailsAndPlayers = await get_room_and_player_details(db, roomUUID)
    } catch(err) {
        logger.error(err);
        return res.status(500).send('INTERNAL ERROR');
    } finally {
        await db.close();
    }

    delete roomDetailsAndPlayers.roomDetails.port;
    delete roomDetailsAndPlayers.roomDetails.pid;
    roomDetailsAndPlayers.userIsOwner = roomDetailsAndPlayers.roomDetails.room_owner === req.session.player_id

    return res.status(200).json(roomDetailsAndPlayers);
}
