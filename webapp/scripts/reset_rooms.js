

const { killProcess } = require("../lib/pyprocess");
const { get_db_connection } = require("../lib/db/get_db_connection");


const destroy = async (db, roomUUID) => {
    console.log("destroying room " + roomUUID);
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
    const db = await get_db_connection();
    let pids = [];
    try {
        const rooms = await db.all("select * from api_room");
        for(let i in rooms) {
            await destroy(db, rooms[i].uuid);
            pids.push(rooms[i].pid)
        }
    } catch (err) {
        throw err;
    } finally {
        db.close();
    }

    for(let i in pids) {
        try {
            killProcess(pids[i]);
        } catch(err) {
            console.error("Got error trying to kill pid " + pids[i]);
            console.error(err);
        }
    }
})();
