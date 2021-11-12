
exports.get_user_count_on_team = async (db, teamUUID) => {
    const statement = await db.prepare(
        'SELECT COUNT(*) as count FROM api_player WHERE team_id = ? COLLATE NOCASE'
    );
    const resp = await statement.get(teamUUID);
    await statement.finalize();
    return resp.count;
}
