
const { get_db_connection } = require("../lib/db/get_db_connection");


(async () => {
    const db = await get_db_connection();
    try {
        const resp = await db.all("select * from api_player");
        console.log("USER TABLE");
        console.table(resp);
    } catch(err) {
        throw err;
    } finally {
        db.close();
    }
})();
