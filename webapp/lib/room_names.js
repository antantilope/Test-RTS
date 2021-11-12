
/*
    Functions to calculate SOCKET.IO Room names
*/

exports.get_rooms_page_name = () => {
    return "rooms_page";
}

exports.get_room_room_name = (roomUUID) => {
    return "room_" + roomUUID;
}

exports.get_team_room_name = (roomUUID, teamUUID) => {
    return "room_" + roomUUID + "_" + teamUUID;
}
