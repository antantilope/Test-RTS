const net = require('net');

const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room_and_player_details } = require("../lib/db/get_rooms");
const { get_rooms_page_name } = require("../lib/room_names");
const { get_user_details } = require("../lib/db/get_user_details");
const { get_map_details } = require ("../lib/db/get_maps");
const { get_unused_port } = require("../lib/db/get_unused_port");
const { mint_room_uuid } = require("../lib/db/mint_room_uuid");
const { mint_team_uuid } = require("../lib/db/mint_team_uuid");
const { spawnPythonSocketServer } = require("../lib/pyprocess");
const {
    EVENT_ROOM_LIST_UPDATE,
} = require("../lib/event_names");
const {
    PHASE_0_LOBBY,
} = require("../constants");
const { logger } = require("../lib/logger")

const create = async (db, room_uuid, team_uuid, port, pid, owner_uuid, room_name, map_uuid, max_players, owner_is_observer) => {
    /*
        Create a room, team, and assign the room owner to the newly created team.
    */
    const sql1 = `
        INSERT INTO api_room
        (uuid, name, battle_map_id, port, pid, max_players, room_owner, phase)
        VALUES (?, ?, ?, ?, ?, ?, ?, "0-lobby")
    `;
    const sql2 = `
        INSERT INTO api_team
        (uuid, room_id, is_observer)
        VALUES (?, ?, ?)
    `;
    const sql3 = `
        UPDATE api_player SET team_id = ? WHERE uuid = ?
    `;
    await Promise.all([
        db.run(sql1, [room_uuid, room_name, map_uuid, port, pid, max_players, owner_uuid]),
        db.run(sql2, [team_uuid, room_uuid, owner_is_observer]),
        db.run(sql3, [team_uuid, owner_uuid]),
    ]);
    return await get_room_and_player_details(db, room_uuid)
}


const setGameMapData = async (port, mapDetails) => {
    const dataToWrite = JSON.stringify({
        set_map: mapDetails
    });
    console.log("writing data to GameServer " + dataToWrite);
    const client = new net.Socket();
    client.on("error", (err) => {
        client.destroy();
        logger.error("set map: could not connect to game server on port " + port);
        logger.error(JSON.stringify(err));
    });
    client.connect(port, 'localhost', () => {
        client.write(dataToWrite + "\n");
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
        console.log({respData})
    });
}


const sendPlayerAndMapDetailsToGameServer = (port, playerName, playerId, teamId, mapDetails) => {
    const client = new net.Socket();
    client.on("error", (err) => {
        client.destroy();
        logger.error("add player: could not connect to game server on port " + port);
        logger.error(JSON.stringify(err));
    });
    client.connect(port, 'localhost', () => {
        const dataToWrite = JSON.stringify({
            add_player: {
                player_name: playerName,
                player_id:playerId,
                team_id: teamId,
            }
        });
        client.write(dataToWrite + "\n");
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
        console.log({respData})
        setTimeout(() => {
            setGameMapData(port, mapDetails);
        }, 500);
    })
}


exports.adminCreateRoomController = async (req, res) => {
    if(!req.session.player_id) {
        return res.sendStatus(401);
    }
    const sess_player_id = req.session.player_id;
    const sess_room_id = req.session.room_id;
    const sess_team_id = req.session.team_id;
    if (sess_room_id || sess_team_id) {
        return res.status(400).send(
            "player already in room"
        );
    }

    const mapUUID = req.body.map_id;
    if (!mapUUID) {
        return res.status(400).send("mapId is required");
    }

    const roomName = req.body.room_name;
    if(!roomName) {
        return res.status(400).send("room_name is required");
    }

    const ownerIsObserver = Boolean(parseInt(req.body.owner_is_observer || "0"))

    const db = await get_db_connection();
    let playerDetails;
    let mapDetails;
    let roomUUID;
    let teamUUID;
    let port;
    let maxPlayers;
    let room;
    try {
        playerDetails = await get_user_details(db, sess_player_id);
        if(!playerDetails.is_superuser) {
            return res.sendStatus(403)
        }
        mapDetails = await get_map_details(db, mapUUID);
        console.log({mapDetails})
        if (mapDetails === null) {
            return res.status(404).send("mapId not found");
        }
        maxPlayers = mapDetails.spawnPoints.length;
        port = await get_unused_port(db);
        roomUUID = await mint_room_uuid(db);
        teamUUID = await mint_team_uuid(db);
        const pythonPID = spawnPythonSocketServer(port);
        room = await create(
            db,
            roomUUID,
            teamUUID,
            port,
            pythonPID,
            sess_player_id,
            roomName,
            mapUUID,
            maxPlayers,
            ownerIsObserver,
        );

    }
    catch(err) {
        logger.error(err)
        return res.sendStatus(500)
    }
    finally {
        db.close();
    }

    // Update player session and complete HTTP request.
    req.session.room_id = roomUUID;
    req.session.team_id = teamUUID;
    res.sendStatus(202);

    // Write data to game server
    setTimeout(() => {
        sendPlayerAndMapDetailsToGameServer(
            port,
            playerDetails.handle,
            playerDetails.uuid,
            teamUUID,
            mapDetails,
        );
    }, 750);

    // Send new room announcement to lobbyists
    setTimeout(() => {
        req.app.get('socketio')
        .to(get_rooms_page_name())
        .emit(
            EVENT_ROOM_LIST_UPDATE,
            {
                uuid: roomUUID,
                name: roomName,
                max_players: maxPlayers,
                player_count: room.roomDetails.player_count,
                phase: PHASE_0_LOBBY,
            },
        );

    }, 800);

}

