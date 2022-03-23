
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_user_details } = require("../lib/db/get_user_details");
const { PHASE_3_COMPLETE } = require("../constants")



function pidIsRunning(pid) {
    try {
      process.kill(pid, 0);
      return true;
    } catch(e) {
      return false;
    }
  }


exports.adminRoomListController = async (req, res) => {
    if(!req.session.player_id){
        return res.sendStatus(401);
    }
    const db = await get_db_connection();
    let user;
    let rooms;
    try {
        user = await get_user_details(db, req.session.player_id)
        if(!user || !user.is_superuser) {
            return res.sendStatus(403);
        }
        rooms = await db.all("SELECT * FROM api_room WHERE phase != ?", [PHASE_3_COMPLETE])
    } catch (err) {
        throw err;
    } finally {
        db.close()
    }
    for(let i in rooms) {
        rooms[i].pidLive = pidIsRunning(rooms[i].pid)
    }
    return res.status(200).json(rooms)
}
