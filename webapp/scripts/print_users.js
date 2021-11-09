
const { get_db_connection } = require("../lib/db/get_db_connection");


(async () => {
    const db = await get_db_connection();
    try {
        const resp = await db.all(`
            SELECT
                api_player.*,
                api_team.room_id as room_id,
                api_team.is_observer as is_observer
            FROM api_player
            LEFT JOIN api_team
            ON api_player.team_id = api_team.uuid
        `);
        console.log(" * * * USER TABLE * * * ");
        console.table(resp);
    } catch(err) {
        throw err;
    } finally {
        db.close();
    }
})();
