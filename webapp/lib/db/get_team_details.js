


exports.get_team_details = async (db, team_uuid) => {
    const sql = `
        SELECT
            api_team.uuid AS team_id,
            count(api_player.team_id) AS player_count
        FROM api_team
        LEFT JOIN api_player
        ON api_team.uuid = api_player.team_id
        WHERE api_team.uuid = ?
        GROUP BY api_team.uuid;
    `;
    const statement = await db.prepare(sql);
    const resp = await statement.get(team_uuid);
    await statement.finalize();
    return resp;
}

