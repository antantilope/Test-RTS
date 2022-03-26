

exports.get_maps = async (db) => {
    let maps = await db.all("SELECT * FROM api_battlemap");
    let mapMines = await db.all("SELECT * FROM api_mapmininglocation");
    let mapStations = await db.all("SELECT * FROM api_mapspacestation");
    let spawnPoints = await db.all("SELECT * FROM api_battlemapspawnpoint");

    let minesByMap = {};
    for(let i in mapMines){
        if((mapMines[i].battle_map_id in minesByMap)) {
            minesByMap[mapMines[i].battle_map_id].push(mapMines[i]);
        } else {
            minesByMap[mapMines[i].battle_map_id] = [
                mapMines[i]
            ];
        }
    }

    let stationsByMap = {};
    for(let i in mapStations){
        if((mapStations[i].battle_map_id in stationsByMap)) {
            stationsByMap[mapStations[i].battle_map_id].push(mapStations[i]);
        } else {
            stationsByMap[mapStations[i].battle_map_id] = [
                mapStations[i]
            ];
        }
    }

    let spawnPointsByMap = {};
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
        maps[i].miningLocations = minesByMap[maps[i].uuid] || [];
        maps[i].spaceStations = stationsByMap[maps[i].uuid] || [];
        maps[i].spawnPoints = spawnPointsByMap[maps[i].uuid] || [];
    }
    return maps;
};

exports.get_map_details = async (db, mapUUID) => {
    let sql, statement;
    sql = `SELECT * FROM api_battlemap WHERE uuid = ?`;
    statement = await db.prepare(sql);
    const mapData = await statement.get(mapUUID);
    await statement.finalize();
    if(!mapData) {
        return null;
    }

    sql = 'SELECT * FROM api_mapmininglocation WHERE battle_map_id = ?';
    const miningLocations = await db.all(sql, [mapUUID]);

    sql = 'SELECT * FROM api_mapspacestation WHERE battle_map_id = ?';
    const spaceStations = await db.all(sql, [mapUUID]);

    sql = 'SELECT * FROM api_battlemapspawnpoint WHERE battle_map_id = ?';
    const spawnPoints = await db.all(sql, [mapUUID]);

    return {
        mapData,
        miningLocations,
        spaceStations,
        spawnPoints,
    };
};
