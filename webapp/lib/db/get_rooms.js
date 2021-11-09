
const { get_db_connection } = require("./get_db_connection")

exports.get_rooms = async () => {
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


exports.get_room = async (db, roomUUID) => {
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
        WHERE api_room.uuid = ?
        GROUP BY api_room.uuid
        LIMIT 1;
    `;
    const statement = await db.prepare(sql);
    const resp = await statement.get(roomUUID);
    await statement.finalize();
    return resp;
}
