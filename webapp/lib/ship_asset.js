

const allAssets = [
    'type_1_blue',
    'type_1_dark_purple',
    'type_1_gray',
    'type_1_green',
    'type_1_light_green',
    'type_1_neon_blue',
    'type_1_orange',
    'type_1_pink',
    'type_1_purple',
    'type_1_red',
    'type_1_yellow',
];

function getRandomAsset() {
    return allAssets[
        Math.floor(Math.random() * allAssets.length)
    ]
}

async function getUnusedShipAssetForRoom(db, roomUUID) {
    const sql = `
        SELECT
            api_player.ship_asset_name AS ship_asset_name
        FROM api_player
        LEFT JOIN api_team ON api_team.uuid = api_player.team_id
        LEFT JOIN api_room ON api_room.uuid = api_team.room_id
        WHERE api_room.uuid = ?;
    `;
    let assetsInUse = await db.all(sql, [roomUUID]);
    assetsInUse = assetsInUse.map(d=>d.ship_asset_name)

    const shuffledAssets = allAssets.sort(
        ()=> Math.random() - Math.random())
    for(i in shuffledAssets) {
        if(assetsInUse.indexOf(shuffledAssets[i]) == -1) {
            return shuffledAssets[i]
        }
    }
    throw new Error("Could not find unused ship asset")
}

exports.getRandomAsset = getRandomAsset;
exports.getUnusedShipAssetForRoom = getUnusedShipAssetForRoom
