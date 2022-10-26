
const { get_db_connection } = require("./get_db_connection")
const { getUnusedAssetForRoom } = require("../ship_asset")

exports.get_rooms = async () => {
    // Get list of rooms for the lobby.
    const sql = `
        SELECT
            api_room.*,
            COUNT(DISTINCT api_team.uuid) as player_count
        FROM api_room
        LEFT JOIN (
            SELECT *
            FROM api_team
            WHERE is_observer = FALSE
        ) api_team
        ON api_team.room_id = api_room.uuid
        WHERE phase = "0-lobby"
        GROUP BY api_room.uuid;
    `;
    const db = await get_db_connection();
    try {

        const rows = await db.all(sql);
        return rows;
    } catch (err) {
        throw err;
    }
    finally {
        db.close();
    }
}


const get_room = async (db, roomUUID) => {
    const sql = `
        SELECT
            api_room.*,
            api_battlemap.name as map_name,
            COUNT(DISTINCT api_team.uuid) as player_count
        FROM api_room
        LEFT JOIN (
            SELECT *
            FROM api_team
            WHERE is_observer = FALSE
        ) api_team
        ON api_team.room_id = api_room.uuid
        LEFT JOIN api_battlemap ON api_battlemap.uuid = api_room.battle_map_id
        WHERE api_room.uuid = ?
        GROUP BY api_room.uuid
        LIMIT 1;
    `;
    const statement = await db.prepare(sql);
    const resp = await statement.get(roomUUID);
    await statement.finalize();
    return resp;
}
exports.get_room = get_room;


exports.get_room_and_player_details = async (db, roomUUID) => {
    const roomDetails = await get_room(db, roomUUID);

    const playersSQL = `
        SELECT
            api_player.uuid AS player_uuid,
            api_player.handle AS handle,
            api_player.team_id AS team_uuid,
            api_player.ship_asset_name as ship_asset_name,
            api_team.is_observer AS is_observer
        FROM api_player
        LEFT JOIN api_team ON api_team.uuid = api_player.team_id
        LEFT JOIN api_room ON api_room.uuid = api_team.room_id
        WHERE api_room.uuid = ?;
    `;
    const players = await db.all(playersSQL, [roomUUID]);

    return {
        roomDetails,
        players,
    }
}
