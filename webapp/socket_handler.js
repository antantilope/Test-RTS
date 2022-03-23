

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
const { logger } = require("./lib/logger");


exports.handleSocketConnection = async (io, socket) => {
    logger.silly("(HI) SOCKET CONNECTED EVENT, ID: " + socket.id);
    socket.on("disconnect", ()=>{
        logger.silly("(BYE) SOCKET DISCONNECTED, ID: " + socket.id)
    });

    sess_player_id = socket.request.session.player_id
    sess_team_id = socket.request.session.team_id
    sess_room_id = socket.request.session.room_id

    if (!sess_player_id)
    {
        logger.warn("disconnecting socket " + socket.id + ", no player_id in session.");
        socket.disconnect(true);
        return
    }
    else if(!sess_team_id && !sess_room_id)
    {
        logger.silly("Adding socket " + socket.id + " to game list room");
        socket.join(get_rooms_page_name());
    }
    else if (sess_team_id && sess_room_id)
    {
        const db = await get_db_connection();
        let roomDetails;
        try {
            roomDetails = await get_room(db, sess_room_id);
            if (typeof roomDetails === 'undefined') {
                logger.warn("disconnecting socket " + socket.id + ", Could not find room");
                socket.disconnect(true);
                return;
            }
        }
        catch (err) {
            throw err;
        }
        finally {
            db.close();
        }

        // Join rooms
        logger.silly("Adding socket " + socket.id + " to game lobby room")
        socket.join(get_room_room_name(sess_room_id));
        if(roomDetails.phase !== PHASE_0_LOBBY) {
            logger.silly("Adding socket " + socket.id + " to game team room")
            socket.join(get_team_room_name(sess_room_id, sess_team_id));
        }

        // Register listener handlers for events from the client
        socket.on(EVENT_PUBMSG, async (message) => {
            logger.info("received " + EVENT_PUBMSG + " event from socket " + socket.id);
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

            logger.silly("emitting event " + EVENT_PUBMSG + " with message " + `${userDetails.handle} ${message}`);
            io.to(get_room_room_name(sess_room_id)).emit(
                EVENT_PUBMSG,
                {
                    sender: userDetails.handle,
                    message,
                },
            );
        });
    }
    else
    {
        logger.error("disconnecting socket, invalid session");
        socket.disconnect(true);
        return;
    }
}
