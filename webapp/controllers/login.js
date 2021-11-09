
const { get_user_from_handle_and_login_code } = require("../lib/db/get_user_from_handle_and_login_code");
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_unused_login_code } = require("../lib/db/get_unused_login_code");
const { set_login_code } = require("../lib/db/set_login_code");
const { MINT_LOGIN_CODE_ON_LOGIN } = require("../constants");


exports.loginWithCodeController = async (req, res) => {
    const handle = req.body.handle;
    const loginCode = req.body.loginCode;

    if (!handle) {
        return res.status(400).send('handle is required');
    }
    if (!loginCode) {
        return res.status(400).send('loginCode is required');
    }

    const db = await get_db_connection();
    try {
        const user = await get_user_from_handle_and_login_code(
            db, handle, loginCode
        );
        if (typeof user === 'undefined') {
            return res.sendStatus(404);
        }

        const newCode = MINT_LOGIN_CODE_ON_LOGIN ? await get_unused_login_code(db) : null;
        await set_login_code(db, user.uuid, newCode);

        req.session.player_id = user.uuid
        req.session.room_id = user.room_id
        req.session.team_id = user.team_id
        req.session.cookie.maxAge = 1 * 24 * 60 * 60 * 1000; // 1 day
        return res.sendStatus(200);

    } catch(err) {
        console.error(err);
        return res.status(500).send('INTERNAL ERROR');

    } finally {
        await db.close();
    }

}
