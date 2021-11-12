
const net = require('net');


(async ()=>{

    const args = process.argv.slice(2);
    const port  = parseInt(args[0]);
    console.log("connecting on port " + port);

    const client = new net.Socket();

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
