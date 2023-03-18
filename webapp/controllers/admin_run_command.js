const { get_db_connection } = require("../lib/db/get_db_connection");
const { getQueueName } = require("../lib/command_queue")

const { get_room } = require("../lib/db/get_rooms");


exports.adminRunCommandController = async (req, res) => {
    if(!req.session.player_id){
        return res.sendStatus(401);
    }
    const room_uuid = req.body.room_uuid;
    if(!room_uuid) {
        return res.status(400).json({msg:"room_uuid is required data"})
    }

    const db = await get_db_connection();
    let user;
    let room;
    try {
        user = await get_user_details(db, req.session.player_id)
        if(!user || !user.is_superuser) {
            return res.sendStatus(403);
        }
        room = await get_room(db, room_uuid);
        if(!room) {
            return res.sendStatus(404);
        }
    } catch (err) {
        throw err;
    } finally {
        db.close();
    }

    const queueName = getQueueName(room.roomDetails.uuid);

    currentQueue = app.get(queueName + '-admin') || []
    currentQueue.push(...req.body.commands)
    app.set(queueName, currentQueue)
}