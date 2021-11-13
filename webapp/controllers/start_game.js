
const net = require('net');

const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room_and_player_details } = require("../lib/db/get_rooms");
const { get_rooms_page_name, get_room_room_name } = require("../lib/room_names");
const { get_user_details } = require("../lib/db/get_user_details");
const { PHASE_1_STARTING, PHASE_2_LIVE } = require("../constants");
const { EVENT_STARTGAME, EVENT_ROOM_LIST_UPDATE  } = require("../lib/event_names");


const doCountdown = (room_id, req, port) => {
    const client = new net.Socket();
    console.log('connecting to GameAPI on port ' + port)
    client.connect(port, 'localhost', () => {
        const dataToWrite = JSON.stringify({decr_phase_1_starting_countdown:{}}) + "\n";
        console.log("writing: " + dataToWrite);
        client.write(dataToWrite);
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
        console.log("countdown data")
        console.log(respData);

        if(respData.ok && respData.phase === PHASE_1_STARTING)
        {
            console.log("COUNT DOWN " + respData.game_start_countdown);
            req.app.get("socketio")
                .to(get_room_room_name(room_id))
                .emit(
                    EVENT_STARTGAME,
                    {game_start_countdown: respData.game_start_countdown},
                );
            if(respData.game_start_countdown - 1 >= 0) {
                console.log("scheduling next countdown");
                setTimeout(()=>{
                    doCountdown(room_id, req, port);
                }, 1000);
            }
        }
        else if (respData.ok && respData.phase === PHASE_2_LIVE)
        {
            console.log("COUNT DOWN 0");
            req.app.get("socketio")
                .to(get_room_room_name(room_id))
                .emit(
                    EVENT_STARTGAME,
                    {game_start_countdown: 0},
                );
        }
    });
}


exports.startGameController = startGameController = async (req, res) => {
    const sess_player_id = req.session.player_id;
    const sess_room_id = req.session.room_id;
    const sess_team_id = req.session.team_id;

    if (!sess_player_id) {
        return res.sendStatus(401);
    }
    if (!sess_room_id && !sess_team_id) {
        return res.status(400).send("session does not contain room_id or team_id");
    }
    if (!sess_room_id || !sess_team_id) {
        return res.status(500).send("invalid session");
    }

    const db = await get_db_connection();
    let playerDetails;
    let room;
    try {
        room = await get_room_and_player_details(db, sess_room_id);
        playerDetails = await get_user_details(db, sess_player_id);
        if(room.roomDetails.room_owner !== sess_player_id) {
            return res.status(400).send("user is not room owner");
        }
        if(room.players.length < 2) {
            return res.status(400).send("not enough players in the room");
        }

        console.log("Updating DB, setting phase = ", PHASE_1_STARTING)
        await db.run(
            'UPDATE api_room SET phase = ? WHERE uuid = ?',
            [PHASE_1_STARTING, room.roomDetails.uuid],
        );
    } catch(err) {
        throw err
    } finally {
        db.close()
    }

    // Return HTTP response.
    res.sendStatus(202);

    // Emit socket event to rooms list page.
    console.log("emitting event to rooms list page")
    req.app.get('socketio')
        .to(get_rooms_page_name())
        .emit(
            EVENT_ROOM_LIST_UPDATE,
            {
                uuid: room.roomDetails.uuid,
                name: room.roomDetails.name,
                max_players: room.roomDetails.max_players,
                player_count: room.roomDetails.player_count,
                phase: PHASE_1_STARTING,
            },
        );


    // Update GameAPI to advance phase to "starting"
    console.log("connecting to game server on port " + room.roomDetails.port);
    const client = new net.Socket();
    client.connect(room.roomDetails.port, 'localhost', () => {
        const dataToWrite = JSON.stringify({advance_to_phase_1_starting:{}}) + "\n";
        console.log("connected, writing " + dataToWrite);
        client.write(dataToWrite);
    });

    client.on("data", data => {
        console.log("got response from GameAPI")
        client.destroy();
        let respData;
        try {
            respData = JSON.parse(data);
        } catch(err) {
            console.error("expected JSON data, got", data);
            throw err;
        }
        console.log("countdown/phase data")
        console.log(respData);

        if(respData.ok && respData.phase === PHASE_1_STARTING) {
            console.log("emitting startgame event")
            req.app.get('socketio')
                .to(get_room_room_name(sess_room_id))
                .emit(
                    EVENT_STARTGAME,
                    {game_start_countdown: respData.game_start_countdown},
                );
            console.log("scheduling next countdown");
            setTimeout(()=>{
                doCountdown(sess_room_id, req, room.roomDetails.port);
            }, 1000);
        }
    });
}
