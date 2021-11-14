
const jwt = require('jsonwebtoken');
const uuid4 = require("uuid4");

const { get_db_connection } = require("../lib/db/get_db_connection");
const locals = require("../applocals");



(async () => {

    const db = await get_db_connection();
    let users;
    try{
        users = await db.all("select * from api_player");
    } catch(err) {
        throw err;
    }
    finally {
        db.close();
    }

    users.forEach(user => {
        const claims = {
            uuid: user.uuid,
            cacheBreaker: uuid4(),
        }
        const token = jwt.sign(claims, locals.sessionKey, { algorithm: 'HS256'});
        console.log(`\n${user.handle}: /loginwithlink?token=${token}\n`);
    });

})();
