
const net = require('net');

const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room_and_player_details } = require("../lib/db/get_rooms");
const { PHASE_1_STARTING } = require("../constants");


module.exports = startGameController = (req, res) => {
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
    try {
        room = await get_room_and_player_details(db, sess_room_id);
        playerDetails = await get_user_details(db, sess_player_id);
        if(room.roomDetails.room_owner !== sess_player_id) {
            return res.status(400).send("user is not room owner");
        }
        if(room.players.length < 2) {
            return res.status(400).send("not enough users");
        }

        await db.run(
            'UPDATE api_room SET phase = ? WHERE uuid = ?',
            [PHASE_1_STARTING, room.roomDetails.uuid],
        );
    } catch(err) {
        throw err
    } finally {
        db.close()
    }


    // Send
    const client = new net.Socket();
    client.connect(room.roomDetails.port, 'localhost', () => {
        console.log(" write " +JSON.stringify({advance_to_phase_1_starting:{}}) + "\n");
        client.write(
            JSON.stringify({advance_to_phase_1_starting:{}}) + "\n"
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
        console.log(respData);
    });
}
