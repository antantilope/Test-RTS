
const tcpPortUsed = require('tcp-port-used');
const net = require('net');

const { get_db_connection } = require("../lib/db/get_db_connection");
const { mint_room_uuid } = require("../lib/db/mint_room_uuid");
const { mint_team_uuid } = require("../lib/db/mint_team_uuid");
const { get_user_details } = require("../lib/db/get_user_details");
const { killProcess,  spawnPythonSocketServer } = require("../lib/pyprocess");
const {
    EVENT_PUBMSG
} = require("../lib/event_names");

const create = async (db, room_uuid, port, pid, owner_uuid, room_name, max_players, owner_is_observer) => {
    /*
        Create a room, team, and assign the room owner to the newly created team.
    */
    const owner_team_uuid = await mint_team_uuid(db);

    const sql1 = `
        INSERT INTO api_room
        (uuid, name, port, pid, max_players, room_owner, phase)
        VALUES (?, ?, ?, ?, ?, ?, "0-lobby")
    `;
    const sql2 = `
        INSERT INTO api_team
        (uuid, room_id, is_observer)
        VALUES (?, ?, ?)
    `;
    const sql3 = `
        UPDATE api_player SET team_id = ? WHERE uuid = ?
    `;
    return Promise.all([
        db.run(sql1, [room_uuid, room_name, port, pid, max_players, owner_uuid]),
        db.run(sql2, [owner_team_uuid, room_uuid, owner_is_observer]),
        db.run(sql3, [owner_team_uuid, owner_uuid]),
    ]);
}


(async ()=>{
    const args = process.argv.slice(2);
    const room_owner  = args[0];
    const room_name = args[1];
    const max_players = parseInt(args[2]);
    const port = parseInt(args[3]); // TODO: automatically calculate this.
    const ownerIsObserver = Boolean(parseInt(args[4]));


    const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        room_owner
    );
    if (!isUUID) {
        throw new Error("Invalid room owner. Expected UUID");
    }
    if(max_players < 2) {
        throw new Error("Invalid max players value");
    }
    if(room_name.length < 3) {
        throw new Error("Room name too short");
    }

    // Validate Port
    if (port > 60000 || port < 2000) {
        throw new Error("Port must be between 2000 and 60000");
    }
    try {
        const portInUse = await tcpPortUsed.check(port, 'localhost');
        if(portInUse) {
            throw new Error();
        } else {
            console.log(`Port ${port} is available!`);
        }
    } catch (err) {
        console.error(err);
        throw new Error("That port is currently in use.");
    }

    // Spawn python socket server process.
    const pythonPID = spawnPythonSocketServer(port);

    // Write changes to database
    const db = await get_db_connection();
    let ownerDetails;
    try {
        ownerDetails = await get_user_details(db, room_owner);
        if (typeof ownerDetails == 'undefined') {
            throw new Error("Room owner not found, id " + room_owner);
        }
        if (ownerDetails.room_uuid || ownerDetails.team_uuid) {
            throw new Error(
                `Room owner already in room/team room: ${ownerDetails.room_uuid} team: ${ownerDetails.team_uuid}`
            );
        }

        const roomUUID = await mint_room_uuid(db);
        const resp = await create(db, roomUUID, port, pythonPID, room_owner, room_name, max_players, ownerIsObserver);
        if (resp.length === resp.filter(r => r.changes === 1).length) {
            console.log("Room Created!");
        } else {
            console.error(resp)
            throw new Error("Unabled to save room to database")
        }

    }
    catch (err) {
        killProcess(pythonPID);
        throw err
    }
    finally {
        db.close();
    }

    setTimeout(() =>{
        // delay this action because the newly spawned
        // socket server will refuse connection if we immediately try to connect to it.
        console.log("Opening connection to game socket on port " + port)
        const client = new net.Socket();
        client.connect(port, 'localhost', () => {
            console.log(" write " + JSON.stringify({add_player:{player_name: ownerDetails.handle, player_id:ownerDetails.uuid}}));
            client.write(
                JSON.stringify({add_player:{player_name: ownerDetails.handle, player_id:ownerDetails.uuid}}) + "\n"
            );
        });
        client.on("data", data => {
            client.destroy();
            let respData;
            try {
                respData = JSON.parse(data);
            } catch(err) {
                console.error("expected JSON data, got", data);
                throw err;
            }
            console.log(respData)
        });
    }, 1000);

})();
