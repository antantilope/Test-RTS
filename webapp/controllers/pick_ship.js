
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room_and_player_details } = require("../lib/db/get_rooms");
const { PHASE_0_LOBBY } = require("../constants");
const { logger } = require("../lib/logger");
const { EVENT_LOBBY_UPDATE } = require("../lib/event_names");
const {
    allAssets,
    getAllUnusedShipAssetsForRoom
} = require("../lib/ship_asset")
const { get_room_room_name } = require("../lib/room_names");

const update = async (db, player_id, ship_asset_name) => {
    const sql = `
        UPDATE api_player SET ship_asset_name = ? WHERE uuid = ?
    `;
    logger.silly("running update query on player " + player_id);
    await db.run(sql, [ship_asset_name, player_id]);
    logger.silly("success!")
}


exports.pickShipController = async (req, res) => {
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
    let roomDetailsAndPlayers;
    try {
        roomDetailsAndPlayers = await get_room_and_player_details(
            db, sess_room_id);
        if(roomDetailsAndPlayers.roomDetails.phase !== PHASE_0_LOBBY) {
            return res.status(400).json({error:"required: ship_asset_name"});
        }
        ship_asset_name = req.body.ship_asset_name;
        if(!ship_asset_name || allAssets.indexOf(ship_asset_name) == -1) {
            return res.status(400).json({error:"unknown ship_asset_name"});
        }
        const available = await getAllUnusedShipAssetsForRoom(db, sess_room_id)
        if(available.indexOf(ship_asset_name) == -1) {
            return res.sendStatus(409);
        }
        await update(db, sess_player_id, ship_asset_name);
        roomDetailsAndPlayers = await get_room_and_player_details(
            db, sess_room_id);
    } catch(err) {
        logger.error(err);
        return res.status(500).send('INTERNAL ERROR');
    } finally {
        await db.close();
    }

    res.sendStatus(200);
    req.app.get('socketio')
    .to(get_room_room_name(roomDetailsAndPlayers.roomDetails.uuid))
    .emit(
        EVENT_LOBBY_UPDATE,
        roomDetailsAndPlayers,
    );
    return;
}
