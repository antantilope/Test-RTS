

exports.get_maps = async (db) => {
    let maps = await db.all("SELECT * FROM api_battlemap");
    let features = await db.all("SELECT * FROM api_battlemapfeature");
    let spawnPoints = await db.all("SELECT * FROM api_battlemapspawnpoint");

    let featuresByMap = {}
    for(let i in features){
        if((features[i].battle_map_id in featuresByMap)) {
            featuresByMap[features[i].battle_map_id].push(features[i]);
        } else {
            featuresByMap[features[i].battle_map_id] = [
                features[i]
            ];
        }
    }

    let spawnPointsByMap = {}
    for(let i in spawnPoints){
        if((spawnPoints[i].battle_map_id in spawnPointsByMap)) {
            spawnPointsByMap[spawnPoints[i].battle_map_id].push(spawnPoints[i]);
        } else {
            spawnPointsByMap[spawnPoints[i].battle_map_id] = [
                spawnPoints[i]
            ];
        }
    }

    for(let i in maps) {
        maps[i].features = featuresByMap[maps[i].uuid] || []
        maps[i].spawn_points = spawnPointsByMap[maps[i].uuid] || []
    }
    return maps
}

exports.get_map_details = async (db, mapUUID) => {
    let sql, statement;
    sql = `SELECT * FROM api_battlemap WHERE uuid = ?`;
    statement = await db.prepare(sql);
    const mapData = await statement.get(mapUUID);
    await statement.finalize();
    if(!mapData) {
        return null
    }

    sql = 'SELECT * FROM api_battlemapfeature WHERE battle_map_id = ?'
    const features = await db.all(sql, [mapUUID]);

    sql = 'SELECT * FROM api_battlemapspawnpoint WHERE battle_map_id = ?'
    const spawnPoints = await db.all(sql, [mapUUID]);

    return {
        mapData,
        features,
        spawnPoints,
    }
}
