

const { get_db_connection } = require("./lib/db/get_db_connection")
const { get_room } = require("./lib/db/get_rooms");
const { get_user_details } = require("./lib/db/get_user_details");
const { get_team_details } = require("./lib/db/get_team_details");
const { removePlayerFromRoom } = require("./controllers/leave_room")
const { PHASE_0_LOBBY, PHASE_2_LIVE } = require("./constants");
const { EVENT_PUBMSG, EVENT_GAME_COMMAND } = require("./lib/event_names");
const {
    get_rooms_page_name,
    get_room_room_name,
    get_team_room_name
} = require("./lib/room_names");
const { getQueueName } = require("./lib/command_queue");
const {
    validateSetHeadingCommand,
    validateSetScannerLockTargetCommand,
    validateRunAutoPilotProgram,
    validateRunAutopilotHeadingToWaypoint,
    validateStartCoreUpgrade,
    validateStartShipUpgrade,
    validateLaunchTubeWeapon,
} = require("./lib/command_validators/validators");
const { CommandValidationError } = require("./lib/command_validators/validation_error");
const { logger } = require("./lib/logger");

const commandHandlers = {
    leave_game: async (app, queueName, session, requestBody) => {
        const sess_player_id = session.player_id;
        const sess_room_id = session.room_id;
        const sess_team_id = session.team_id;
        const db = await get_db_connection();
        try {
            roomDetails = await get_room(db, sess_room_id);
            if(roomDetails.phase != PHASE_2_LIVE){
                return
            }
            const teamDetails = await get_team_details(db, sess_team_id);
            const deleteTeam = teamDetails.player_count === 1;
            await removePlayerFromRoom(db, sess_player_id, sess_team_id, deleteTeam);
        } catch (err) {
            throw err
        } finally {
            db.close()
        }
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'leave_game',
        });
    },
    set_heading: (app, queueName, session, requestBody) => {
        const validatedData = validateSetHeadingCommand(requestBody);
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'set_heading',
            args: [validatedData.heading],
        });
    },
    activate_engine: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'activate_engine',
        });
    },
    deactivate_engine: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'deactivate_engine',
        });
    },
    light_engine: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'light_engine',
        });
    },
    boost_engine: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'boost_engine',
        });
    },
    unlight_engine: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'unlight_engine',
        });
    },
    activate_apu: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'activate_apu',
        });
    },
    deactivate_apu: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'deactivate_apu',
        });
    },
    activate_scanner: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'activate_scanner',
        });
    },
    deactivate_scanner: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'deactivate_scanner',
        });
    },
    set_scanner_mode_radar: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'set_scanner_mode_radar',
        });
    },
    set_scanner_mode_ir: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'set_scanner_mode_ir',
        });
    },
    set_scanner_lock_target: (app, queueName, session, requestBody) => {
        const validatedData = validateSetScannerLockTargetCommand(requestBody);
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'set_scanner_lock_target',
            args: [validatedData.target],
        });
    },
    charge_ebeam: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'charge_ebeam',
        });
    },
    pause_charge_ebeam: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'pause_charge_ebeam',
        });
    },
    fire_ebeam: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'fire_ebeam',
        });
    },
    run_autopilot: (app, queueName, session, requestBody) => {
        const data = validateRunAutoPilotProgram(requestBody);
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'run_autopilot',
            args:[data.autopilot_program],
        });
    },
    run_autopilot_heading_to_waypoint: (app, queueName, session, requestBody) => {
        const kwargs = validateRunAutopilotHeadingToWaypoint(requestBody)
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'run_autopilot_heading_to_waypoint',
            kwargs,
        });
    },
    disable_autopilot: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'disable_autopilot',
        });
    },
    extend_gravity_brake: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'extend_gravity_brake',
        });
    },
    retract_gravity_brake: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'retract_gravity_brake',
        });
    },
    start_ore_mining: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'start_ore_mining',
        });
    },
    stop_ore_mining: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'stop_ore_mining',
        });
    },
    start_fueling: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'start_fueling',
        });
    },
    stop_fueling: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'stop_fueling',
        });
    },
    trade_ore_for_ore_coin: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'trade_ore_for_ore_coin',
        });
    },
    start_core_upgrade: (app, queueName, session, requestBody) => {
        const slug = validateStartCoreUpgrade(requestBody);
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'start_core_upgrade',
            args: [slug],
        });
    },
    start_ship_upgrade: (app, queueName, session, requestBody) => {
        const slug = validateStartShipUpgrade(requestBody);
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'start_ship_upgrade',
            args: [slug],
        });
    },
    cancel_core_upgrade: (app, queueName, session, requestBody) => {
        const slug = validateStartCoreUpgrade(requestBody);
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'cancel_core_upgrade',
            args: [slug],
        });
    },
    cancel_ship_upgrade: (app, queueName, session, requestBody) => {
        const slug = validateStartShipUpgrade(requestBody);
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'cancel_ship_upgrade',
            args: [slug],
        });
    },
    buy_magnet_mine: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'buy_magnet_mine',
        });
    },
    launch_magnet_mine: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'launch_magnet_mine',
        });
    },
    buy_emp: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'buy_emp',
        });
    },
    launch_emp: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'launch_emp',
        });
    },
    buy_hunter_drone: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'buy_hunter_drone',
        });
    },
    launch_hunter_drone: (app, queueName, session, requestBody) => {
        app.get(queueName).push({
            player_id: session.player_id,
            ship_command: 'launch_hunter_drone',
        });
    },
};


exports.handleSocketConnection = async (io, socket, app) => {
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

        socket.on(EVENT_GAME_COMMAND, async (command, requestBody)=>{
            const queueName = getQueueName(sess_room_id)
            if(!app.get(queueName)) {
                const db = await get_db_connection();
                let room;
                try {
                    room = await get_room(db, sess_room_id);
                    if (typeof room === 'undefined') {
                        logger.error("Could not find room with id " + sess_room_id)
                        return
                    }
                }
                catch (err) {
                    throw err;
                }
                finally {
                    db.close();
                }
                if (room.phase === PHASE_2_LIVE) {
                    logger.warn("Express App command queue not set for live room, adding...")
                    app.set(queueName, []);
                }
                else {
                    logger.error(
                        "Room's command queue is not set, and room is not in live phase."
                    );
                    return;
                }
            }
            if(!command) {
                logger.warn("Received game command event with no command");
                return;
            }
            if(!requestBody) {
                logger.warn("Received game command event with no requestBody");
                return;
            }
            const handler = commandHandlers[command];
            if(typeof handler === "undefined") {
                logger.warn("Received unknown game command " + command);
                return;
            }
            try {
                handler(app, queueName, socket.request.session, requestBody);
            } catch (e) {
                if(e instanceof CommandValidationError) {
                    logger.warn("command " + command + " caused CommandValidationError");
                    return;
                }
                else {
                    logger.error(e);
                    return;
                }
            }
        })
    }
    else
    {
        logger.error("disconnecting socket, invalid session");
        socket.disconnect(true);
        return;
    }
}
