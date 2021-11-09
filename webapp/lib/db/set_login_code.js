
exports.set_login_code = async (db, uuid, newCode) => {
    const sql = 'UPDATE api_player set login_code = ? where uuid = ?'
    const resp = await db.run(sql, [newCode, uuid]);
    return resp;
}

