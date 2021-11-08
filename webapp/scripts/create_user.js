
const { get_unused_login_code } = require("../lib/db/get_unused_login_code");
const { get_db_connection } = require("../lib/db/get_db_connection");
const { user_handle_exists } = require("../lib/db/user_handle_exists");
const { mint_user_uuid } = require("../lib/db/mint_user_uuid");
const { create_user }  = require("../lib/db/create_user");



(async function(){

    const args = process.argv.slice(2);
    const handle = args[0];

    const db = await get_db_connection();
    try {

        const loginCode = await get_unused_login_code(db);
        const handleAlreadyExists = await user_handle_exists(db, handle);
        if (handleAlreadyExists) {
            throw new Error("user with handle already exists")
        }
        const newUUID = await mint_user_uuid(db);

        const newUserResp = await create_user(db, newUUID, handle, loginCode, false);
        if (newUserResp.changes) {
            console.log("Created new user! Login code is " + loginCode);
        } else {
            console.error(newUserResp);
            throw new Error("Unable to create super user")
        }

    } catch(err) {
        throw err;
    } finally {
        db.close();
    }

})();
