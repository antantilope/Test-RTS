

exports.get_user_details = async (db, player_uuid) => {
    const sql = `
        SELECT
            api_player.uuid AS uuid,
            api_player.handle AS handle,
            api_player.team_id AS team_uuid,
            api_player.is_superuser AS is_superuser,
            api_team.is_observer AS is_observer,
            api_room.uuid AS room_uuid,
            api_room.max_players AS room_max_players,
            api_room.room_owner AS room_owner,
            api_room.phase AS room_phase
        FROM api_player
        LEFT JOIN api_team on api_player.team_id = api_team.uuid
        LEFT JOIN api_room on api_team.room_id = api_room.uuid
        WHERE api_player.uuid = ?
    `
    const statement = await db.prepare(sql);
    const resp = await statement.get(player_uuid);
    await statement.finalize();
    return resp;
}
