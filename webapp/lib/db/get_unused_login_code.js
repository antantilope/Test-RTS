

const getRandomLoginCode = () => {
    const min = 10000;
    const max = 99999;
    return Math.floor(Math.random() * (max - min) + min);
}


exports.get_unused_login_code = async (db) => {
    let attempts = 0;
    const maxAttempts = 10;
    const triedValues = [];
    while (attempts <= maxAttempts)
    {
        attempts++;
        let newLoginCode = getRandomLoginCode();
        const statement = await db.prepare('SELECT COUNT(*) as count FROM api_player WHERE login_code = ?');
        const resp = await statement.get(newLoginCode);
        await statement.finalize();
        const count = resp.count;
        if (count === 0)
        {
            return newLoginCode;
        } else
        {
            triedValues.push(newLoginCode);
            console.warn("Generated code is not unique " + newLoginCode);
        }
    }
    throw new Error(
        `could not generate unused login code, tried values ${triedValues}.`
    );
}
