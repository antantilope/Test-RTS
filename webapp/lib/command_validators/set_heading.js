
const { CommandValidationError } = require("./validation_error");


const validateSetHeadingCommand = (data) => {
    const heading = parseInt(data.heading);
    if(isNaN(heading) || heading > 359 || heading < 0) {
        throw new CommandValidationError("invalid heading")
    }
    return {heading}
}

exports.validateSetHeadingCommand = validateSetHeadingCommand;
