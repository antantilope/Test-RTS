
const path = require('path');
const sqlite = require('sqlite-async')


const fullPath = path.join(__dirname, '../../appmodels/db.sqlite3');


exports.get_db_connection = async () => {
    return await sqlite.open(fullPath);
}
