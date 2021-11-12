
exports.set_login_code = async (db, uuid, newCode) => {
    const sql = 'UPDATE api_player SET login_code = ? WHERE uuid = ?'
    const resp = await db.run(sql, [newCode, uuid]);
    return resp;
}

