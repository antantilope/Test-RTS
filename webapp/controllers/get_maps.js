
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_maps } = require("../lib/db/get_maps");
const { logger } = require("../lib/logger");

exports.getMapsController = async (req, res) => {
    if(!req.session.player_id) {
        return res.sendStatus(401);
    }
    const db = await get_db_connection();
    let maps;
    try {
        maps = await get_maps(db);
    }catch(err) {
        logger.error(err);
        return res.status(500).send('INTERNAL ERROR');
    } finally {
        await db.close();
    }
    return res.status(200).json(maps);
}
