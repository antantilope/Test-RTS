
const {
    EVENT_ROOM_LIST_UPDATE,
    EVENT_LOBBY_UPDATE,
} = require("../lib/event_names");
const { get_rooms_page_name } = require("../lib/room_names");
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_user_details } = require("../lib/db/get_user_details");
const { get_room } = require("../lib/db/get_rooms");
const { logger } = require("../lib/logger");

function pidIsRunning(pid) {
    try {
        process.kill(pid, 0);
        return true;
    } catch(e) {
        return false;
    }
}

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

exports.adminRoomDeleteController = async (req, res) => {
    if(!req.session.player_id){
        return res.sendStatus(401);
    }
    const room_uuid = req.body.room_uuid;
    if(!room_uuid) {
        return res.status(400).send("room_uuid is required data")
    }
    const db = await get_db_connection();
    let user;
    let room;
    let pid;
    try {
        user = await get_user_details(db, req.session.player_id)
        if(!user || !user.is_superuser) {
            return res.sendStatus(403);
        }
        room = await get_room(db, room_uuid);
        if(!room) {
            return res.sendStatus(404);
        }
        pid = room.pid
        await destroy(db, room_uuid);
    } catch (err) {
        throw err;
    } finally {
        db.close()
    }

    let msg = "ok";
    if(pidIsRunning(pid)) {
        try{
            process.kill(pid);
        } catch(err) {
            logger.warn("could not kill process");
            logger.warn(err);
            msg = "could not kill process"
        }
    }

    req.app.get('socketio')
    .to(get_rooms_page_name())
    .emit(
        EVENT_ROOM_LIST_UPDATE,
        {
            uuid: room.uuid,
            remove: true,
        },
    );

    return res.status(200).json({msg})
}
