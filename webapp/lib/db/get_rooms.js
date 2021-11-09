
const { get_db_connection } = require("./get_db_connection")

exports.get_rooms = async () => {
    const db = await get_db_connection();
    const sql = `SELECT * FROM api_room`
    const rows = await db.all(sql)


}