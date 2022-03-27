const TWO_PI = 2 * Math.PI

function drawMapPreview(mapData, canvas) {
    const ctx = canvas.getContext("2d");
    const yOffset = 20;
    const metersPerCanvasPxX = mapData.meters_x / canvas.width;
    const metersPerCanvasPxY = mapData.meters_y / (canvas.height - yOffset);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.beginPath();
    ctx.font = "16px Courier New";
    ctx.fillStyle = '#000000';
    ctx.textAlign = 'left';
    ctx.textBaseline = "middle";
    ctx.fillText(
        `${mapData.name} (${Math.floor(mapData.meters_x / 1000)}km x ${Math.floor(mapData.meters_y / 1000)}km)`,
        10,
        yOffset / 2,
    );

    ctx.beginPath();
    ctx.fillStyle = "#000000";
    ctx.rect(0, yOffset, canvas.width, canvas.height);
    ctx.fill();

    for(let i=0; i<mapData.spawnPoints.length; i++) {
        let spCx = mapData.spawnPoints[i].position_meters_x / metersPerCanvasPxX;
        let spCy = mapData.spawnPoints[i].position_meters_y / metersPerCanvasPxY;
        console.log({
            sp: mapData.spawnPoints[i],
            ch: canvas.height,
            spCx,
            spCy,
            metersPerCanvasPxY,
        })
        ctx.beginPath();
        ctx.strokeStyle = "#00ff00"
        ctx.lineWidth = 3
        ctx.arc(
            spCx, (canvas.height - spCy), 7, 0, TWO_PI
        );
        ctx.stroke();
    }

    for(let i=0; i<mapData.spaceStations.length; i++) {
        let fCx = mapData.spaceStations[i].position_meters_x / metersPerCanvasPxX;
        let fCy = mapData.spaceStations[i].position_meters_y / metersPerCanvasPxY;
        let icon = "🛰️";
        ctx.beginPath();
        ctx.font = "20px Courier New";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = 'center';
        ctx.textBaseline = "middle";
        ctx.fillText(
            icon,
            fCx,
            (canvas.height - fCy),
        );
    }

    ctx.font = "20px Courier New";
    ctx.fillStyle = "#ffffff";
    ctx.textAlign = 'center';
    ctx.textBaseline = "middle";
    for(let i=0; i<mapData.spaceStations.length; i++) {
        let fCx = mapData.spaceStations[i].position_meters_x / metersPerCanvasPxX;
        let fCy = mapData.spaceStations[i].position_meters_y / metersPerCanvasPxY;
        let icon = "🛰️";
        ctx.beginPath();
        ctx.fillText(
            icon,
            fCx,
            (canvas.height - fCy),
        );
    }

    for(let i=0; i<mapData.miningLocations.length; i++) {
        let fCx = mapData.miningLocations[i].position_meters_x / metersPerCanvasPxX;
        let fCy = mapData.miningLocations[i].position_meters_y / metersPerCanvasPxY;
        let icon = "💎";
        ctx.beginPath();
        ctx.fillText(
            icon,
            fCx,
            (canvas.height - fCy),
        );
    }

}
