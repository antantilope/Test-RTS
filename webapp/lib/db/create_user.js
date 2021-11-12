

exports.create_user = async (db, newUUID, handle, loginCode, isSuperuser) => {
    const sql = 'INSERT INTO api_player (uuid, handle, login_code, is_superuser) VALUES (?, ?, ?, ?)'
    const resp = await db.run(sql, [newUUID, handle, loginCode, isSuperuser]);
    return resp;
}

