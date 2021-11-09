

const { get_unused_login_code } = require("../lib/db/get_unused_login_code");
const { get_db_connection } = require("../lib/db/get_db_connection");
const { set_login_code } = require("../lib/db/set_login_code");



(async function(){

    const args = process.argv.slice(2);
    const handleOrUUID = args[0];

    const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        handleOrUUID
    );

    const sql = isUUID ?
        'SELECT uuid FROM api_player WHERE uuid = ? COLLATE NOCASE'
        : 'SELECT uuid from api_player WHERE handle = ? COLLATE NOCASE';

    const db = await get_db_connection();
    try {
        const statement = await db.prepare(sql);
        const resp = await statement.get(handleOrUUID);
        await statement.finalize();
        if (typeof resp !== 'undefined' && resp) {
            const uuid = resp.uuid;
            const newLoginCode = await get_unused_login_code(db);
            const updateResp = await set_login_code(db, uuid, newLoginCode);
            if (typeof updateResp !== 'undefined' && updateResp && updateResp.changes) {
                console.log("login code set to " + newLoginCode);
            } else {
                console.error(updateResp);
                throw new Error("Could save new login code");
            }
        } else {
            throw new Error("Could not find player using sql " + sql)
        }

    } catch(err) {
        throw err;
    } finally {
        db.close();
    }

})()