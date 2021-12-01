
const { get_db_connection } = require("../lib/db/get_db_connection");
const { get_room } = require("../lib/db/get_rooms");
const { getQueueName } = require("../lib/command_queue");
const { PHASE_2_LIVE } = require("../constants")
const { logger } = require("../lib/logger");
const { CommandValidationError } = require("../lib/command_validators/validation_error");
const { validateSetHeadingCommand } = require("../lib/command_validators/set_heading");


const commandHandlers = {
    set_heading: (req, queueName) => {
        const validatedData = validateSetHeadingCommand(req.body);
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'set_heading',
            args: [validatedData.heading],
        });
    },
    activate_reaction_wheel: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'activate_reaction_wheel',
        });
    },
    deactivate_reaction_wheel: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'deactivate_reaction_wheel',
        });
    },
    activate_engine: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'activate_engine',
        });
    },
    deactivate_engine: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'deactivate_engine',
        });
    },
    light_engine: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'light_engine',
        });
    },
    unlight_engine: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'unlight_engine',
        });
    },
    activate_scanner: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'activate_scanner',
        });
    },
    deactivate_scanner: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'deactivate_scanner',
        });
    },
    set_scanner_mode_radar: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'set_scanner_mode_radar',
        });
    },
    set_scanner_mode_ir: (req, queueName) => {
        req.app.get(queueName).push({
            player_id: req.session.player_id,
            ship_command: 'set_scanner_mode_ir',
        });
    },
};

exports.RunCommandController = async (req, res) => {
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

    const queueName = getQueueName(sess_room_id)
    if(!req.app.get(queueName)) {
        const db = await get_db_connection();
        let room;
        try {
            room = await get_room(db, sess_room_id);
            if (typeof room === 'undefined') {
                console.error("Unable To Find room");
                return res.status(500).send("Could not find room with id " + sess_room_id)
            }
        }
        catch (err) {
            throw err;
        }
        finally {
            db.close()
        }
        if (room.phase === PHASE_2_LIVE) {
            logger.warn("Express App command queue not set for live room, adding...")
            req.app.set(queueName, []);
        }
        else {
            return res.status(400).send(
                "Room's command queue is not set, and room is not in live phase."
            );
        }
    }

    const command = req.body.command;
    if(!command) {
        return res.sendStatus(400)
    }
    const handler = commandHandlers[command];
    if(typeof handler === "undefined") {
        return res.status(400).send("unknown command")
    }
    try {
        handler(req, queueName);
    } catch (e) {
        if(e instanceof CommandValidationError) {
            return res.sendStatus(400);
        }
        else {
            logger.error(e);
            return res.sendStatus(500);
        }
    }

    return res.status(202).json({})
}
