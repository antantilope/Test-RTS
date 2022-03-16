
const { CommandValidationError } = require("./validation_error");


const validateSetHeadingCommand = (data) => {
    const heading = parseInt(data.heading);
    if(isNaN(heading) || heading > 359 || heading < 0) {
        throw new CommandValidationError("invalid heading")
    }
    return {heading}
}

const validateSetScannerLockTargetCommand = (data) => {
    const uuid = data.target
    if (!uuid) {
        throw new CommandValidationError("invalid target")
    }
    if (!/^[a-f0-9]+$/.test(uuid)) {
        throw new CommandValidationError("invalid target value")
    }
    if(uuid.length < 30) {
        throw new CommandValidationError("invalid target value L")
    }
    return {target: uuid}
}

const validateRunAutoPilotProgram = (data) => {
    const programs = [
        "position_hold", "lock_target", "lock_prograde", "lock_retrograde"
    ]
    const autopilot_program = data.autopilot_program;
    if (!autopilot_program) {
        throw new CommandValidationError("invalid program");
    }
    if(programs.indexOf(autopilot_program) == -1) {
        throw new CommandValidationError("invalid program");
    }
    return { autopilot_program };
}

exports.validateSetHeadingCommand = validateSetHeadingCommand;
exports.validateSetScannerLockTargetCommand = validateSetScannerLockTargetCommand;
exports.validateRunAutoPilotProgram = validateRunAutoPilotProgram;
