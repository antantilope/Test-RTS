
const { get_user_details } = require("../lib/db/get_user_details")
const { get_db_connection } = require("../lib/db/get_db_connection");
const { logger } = require("../lib/logger");


exports.userDetailsController = async (req, res) => {
    const sess_player_id = req.session.player_id;
    if (!sess_player_id) {
        return res.sendStatus(401);
    }
    const db = await get_db_connection();
    let playerDetails;
    try {
        playerDetails = await get_user_details(db, sess_player_id);
    } catch(err) {
        throw err
    } finally {
        db.close()
    }

    if(typeof playerDetails === 'undefined') {
        logger.error("Expected to find user uuid but could not.")
        return res.sendStatus(500);
    }

    return res.status(200).json({
        uuid: playerDetails.uuid,
        handle: playerDetails.handle,
        is_superuser: playerDetails.is_superuser,
    });
}

