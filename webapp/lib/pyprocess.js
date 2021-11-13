
const path = require("path");
const { spawn } = require("child_process");
const { kill } = require("process");

const { logger } = require("./logger");


exports.killProcess = (pid) => {
    logger.info("killing process " + pid);
    kill(pid, 'SIGHUP');
}

exports.spawnPythonSocketServer = (port) => {
    const commandRoot = './env/bin/python';
    const cpArgs = ['-m', 'api.main', port, ]
    const cwd = path.join(__dirname, "../../");
    logger.info("spawning python process")
    logger.info(JSON.stringify({cwd, commandRoot, cpArgs}));
    const cp = spawn(commandRoot, cpArgs, {
        cwd,
        detached: true,
        stdio: 'ignore',
    });
    const pid = cp.pid
    logger.info("process launched, pid: " + pid);
    cp.unref();
    return pid;
}

