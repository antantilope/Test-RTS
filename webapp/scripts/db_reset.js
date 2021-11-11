
const { get_db_connection } = require("../lib/db/get_db_connection");
const { createClient } = require('redis');
const util = require('util');




(async function(){
    console.log("resetting DB");

    const db = await get_db_connection();
    try {
        await db.run('UPDATE api_player SET team_id = NULL;');
        await db.run('DELETE FROM api_team;');
        await db.run('DELETE FROM api_room;');
        console.log("Done!");
    } catch(err) {
        throw err;
    } finally {
        db.close();
    }


})().then(()=>{
    console.log("Resetting Redis Session");

    const clearSession = () => {
        const client = createClient();
        client.on('error', (err) => console.log('Redis Client Error', err));

        const isExpressSession = key => {
            return key.slice(0, 5) === 'sess:';
        };
        client.keys("*", (err, keys) => {
            keys.filter(isExpressSession).forEach(key => {
                console.log("deleting key " + key);
                client.del(key, (err, resp => {
                    console.log({err, resp});
                }));
            });
        });
    }
    clearSession();
    setTimeout(() =>{
        console.log("bye!")
        process.exit(0);
    }, 1000);

});


