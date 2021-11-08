
exports.user_handle_exists = async (db, handle) => {
    const statement = await db.prepare(
        'SELECT COUNT(*) as count FROM api_player WHERE handle = ? COLLATE NOCASE'
    );
    const resp = await statement.get(handle);
    await statement.finalize();
    return resp.count > 0;
}
