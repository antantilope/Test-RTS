
const { get_db_connection } = require("../lib/db/get_db_connection");


(async () => {
    const db = await get_db_connection();
    try {
        const resp = await db.all(`
            SELECT * FROM api_room;
        `);
        console.log(" * * * ROOM TABLE * * * ");
        console.table(resp);
    } catch(err) {
        throw err;
    } finally {
        db.close();
    }
})();
