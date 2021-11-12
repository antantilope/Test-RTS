

const uuid4  = require("uuid4");


exports.mint_room_uuid = async (db) => {
    while(true) {
        const newUUID = uuid4();
        const statement = await db.prepare(
            'SELECT COUNT(*) as count FROM api_room WHERE uuid = ? COLLATE NOCASE'
        );
        const resp = await statement.get(newUUID);
        await statement.finalize();
        if (resp.count === 0) {
            return newUUID;
        }
        else {
            console.warn("Could not mint room UUID, found duplicate for id " + newUUID);
        }
    }
}

