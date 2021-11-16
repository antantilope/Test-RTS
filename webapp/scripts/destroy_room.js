
const { killProcess } = require("../lib/pyprocess");
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room } = require("../lib/db/get_rooms");


const destroy = async (db, roomUUID) => {
    sql1 = `
        UPDATE api_player SET team_id = NULL WHERE team_id IN (
            SELECT uuid FROM api_team WHERE room_id = ?
        );
    `;
    sql2 = `
        DELETE FROM api_team WHERE room_id = ?;
    `;
    sql3 = `
        DELETE FROM api_room WHERE uuid = ?;
    `;

    await db.run(sql1, [roomUUID]);
    await db.run(sql2, [roomUUID]);
    await db.run(sql3, [roomUUID]);

}


(async ()=>{

    const args = process.argv.slice(2);
    const roomUUID  = args[0];
    const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        roomUUID
    );
    if (!isUUID) {
        throw new Error("Invalid room UUID. Expected UUID");
    }


    const db = await get_db_connection();
    let room;
    try {
        room = await get_room(db, roomUUID);
        if (typeof room === 'undefined') {
            throw new Error("Room not found, id " + roomUUID);
        }
        await destroy(db, roomUUID);
    } catch (err) {
        throw err;
    } finally {
        db.close();
    }

    killProcess(room.pid);

})();
