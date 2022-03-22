
const net = require('net');


(async ()=>{

    const args = process.argv.slice(2);
    const port  = parseInt(args[0]);
    console.log("connecting on port " + port);

    const client = new net.Socket();

    client.on("error", (err) => {
        client.destroy();
        console.error("test : could not connect to game server on port " + port);
        console.error(JSON.stringify(err));
    });

    client.connect(port, 'localhost', () => {
        console.log("connected!, sending ping...");
        client.write('{"ping":{}}\n');
    });

    client.on("data", data => {
        console.log('Received back: ' + data);
        client.destroy();
    });

    client.on('close', () => {
        console.log('Connection closed');
    });

})();
