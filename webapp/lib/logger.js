
const winston = require("winston");

const winstonColors = {
    error: "red",
    warn: "yellow",
    info: "blue",
    http: "cyan",
    verbose:"green",
    debug:"green",
    silly:"green",
};
winston.addColors(winstonColors);
const myFormat = winston.format.printf(info => {
    return `${info.timestamp} ${info.level}: ${info.message}`;
});
const fileFormat = winston.format.combine(
    winston.format.timestamp(),
    myFormat
);
const terminalFormat = winston.format.combine(
    winston.format.colorize(),
    winston.format.timestamp(),
    myFormat
);
const logger = winston.createLogger({
    transports: [
        new winston.transports.File(
            {
                filename: 'error.log',
                level: 'error',
                format: fileFormat
            }
        ),
        new winston.transports.File(
            {
                filename: 'combined.log',
                level:'info',
                format:fileFormat
            }
        ),
        new winston.transports.Console(
            {
                level: 'silly',
                prettyPrint: true,
                colorize: true,
                silent: false,
                timestamp: true,
                format:terminalFormat
            }
        ),
    ]
});


logger.info("logger created 🛠️");


exports.logger = logger;
