
const path = require("path");
const { spawn } = require("child_process");
const { kill } = require("process");


exports.killProcess = (pid) => {
    kill(pid, 'SIGHUP');
}

exports.spawnPythonSocketServer = (port) => {
    const commandRoot = './env/bin/python';
    const cpArgs = ['-m', 'api.main', port, ]
    const cwd = path.join(__dirname, "../../");
    console.log({cwd, commandRoot, cpArgs});
    const cp = spawn(commandRoot, cpArgs, {
        cwd,
        detached: true,
        stdio: 'ignore',
    });
    const pid = cp.pid
    console.log("process launched, pid: " + pid);
    cp.unref();
    return pid;
}

