
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

exports.validateSetHeadingCommand = validateSetHeadingCommand;
exports.validateSetScannerLockTargetCommand = validateSetScannerLockTargetCommand
