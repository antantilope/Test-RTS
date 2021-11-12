

const { get_db_connection } = require("./lib/db/get_db_connection")
const { get_room } = require("./lib/db/get_rooms");
const { get_user_details } = require("./lib/db/get_user_details");
const { PHASE_0_LOBBY } = require("./constants");
const { EVENT_PUBMSG } = require("./lib/event_names");

const {
    get_rooms_page_name,
    get_room_room_name,
    get_team_room_name
} = require("./lib/room_names");


exports.handleSocketConnection = async (io, socket) => {
    console.log("socket connected, ID: " + socket.id);
    socket.on("disconnect", ()=>{
        socket.rooms
        console.log("socket disconnected, ID: " + socket.id)
    });

    sess_player_id = socket.request.session.player_id
    sess_team_id = socket.request.session.team_id
    sess_room_id = socket.request.session.room_id

    if (!sess_player_id)
    {
        console.error("disconnecting socket, no player_id in session.");
        socket.disconnect(true);
        return
    }
    else if(!sess_team_id && !sess_room_id)
    {
        socket.join(get_rooms_page_name());
    }
    else if (sess_team_id && sess_room_id)
    {
        const db = await get_db_connection();
        let roomDetails;
        try {
            roomDetails = await get_room(db, sess_room_id);
            if (typeof roomDetails === 'undefined') {
                throw new Error("could not find room");
            }
        }
        catch (err) {
            throw err;
        }
        finally {
            db.close();
        }
        // Join rooms
        socket.join(get_room_room_name(sess_room_id));
        if(roomDetails.phase !== PHASE_0_LOBBY) {
            console.log("adding socket to team room")
            socket.join(get_team_room_name(sess_room_id, sess_team_id));
        }

        // Register listener handlers for events from the client
        socket.on(EVENT_PUBMSG, async (message) => {
            const db = await get_db_connection()
            let userDetails;
            try {
                userDetails = await get_user_details(db, socket.request.session.player_id);
            }
            catch(err) {
                throw err;
            }
            finally {
                db.close();
            }
            console.log({pubmsg: message});
            console.log({session: socket.request.session});
            const outmsg = `${userDetails.handle} 💬 ${message}`;
            console.log(outmsg);
            console.log()
            io.to(get_room_room_name(sess_room_id)).emit(
                EVENT_PUBMSG,
                outmsg,
            );
        });
    }
    else
    {
        console.error("disconnecting socket, invalid session");
        console.error(socket.request.session);
        socket.disconnect(true);
        return;
    }
}
