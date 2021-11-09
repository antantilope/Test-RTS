
exports.get_user_from_handle_and_login_code = async (db, handle, loginCode) => {
    const statement = await db.prepare(
        `
            SELECT
                api_player.*,
                api_team.room_id as room_id
            FROM api_player
            LEFT JOIN api_team ON api_player.team_id = api_team.uuid
            WHERE handle = ? AND login_code = ? LIMIT 1
        `
    );
    const response = await statement.get(handle, loginCode);
    await statement.finalize();
    return response
}
