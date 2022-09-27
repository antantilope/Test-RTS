

function getValidPort() {
    const portMin = 2000;
    const portMax = 65000;
    const portsToNeverUse = [
        3000, 5000, 8000, // common development ports
        4000, 8080, 9000, // "
        3306,             // mysql
        6379,             // redis
        5432, 5433,       // postgres
    ];
    const port = Math.floor(Math.random() * (portMax - portMin) + portMin);
    if(portsToNeverUse.indexOf(port) == -1) {
        return port;
    }
    return getValidPort(); // try again
}

async function get_unused_port(db) {
    let attempts = 1;
    while(attempts < 4) {
        const port = getValidPort()
        const sql = 'SELECT COUNT(*) as count FROM api_room WHERE port = ?';
        const statement = await db.prepare(sql);
        const resp = await statement.get(port);
        await statement.finalize();
        if(resp.count === 0) {
            return port;
        }
        attempts++;
    }
    throw new Error("Could not find unused port");
}

exports.get_unused_port = get_unused_port;
