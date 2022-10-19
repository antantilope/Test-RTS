
const { CommandValidationError } = require("./validation_error");


const validateSetHeadingCommand = (data) => {
    const heading = parseInt(data.heading);
    if(isNaN(heading) || heading > 359 || heading < 0) {
        throw new CommandValidationError("invalid heading")
    }
    return {heading}
}

const validateSetScannerLockTargetCommand = (data) => {
    const uuid = data.target
    if (!uuid) {
        throw new CommandValidationError("invalid target")
    }
    if (!/^[a-f0-9]+$/.test(uuid)) {
        throw new CommandValidationError("invalid target value")
    }
    if(uuid.length < 30) {
        throw new CommandValidationError("invalid target value L")
    }
    return {target: uuid}
}

const validateRunAutoPilotProgram = (data) => {
    const programs = [
        "position_hold", "lock_target", "lock_prograde", "lock_retrograde"
    ]
    const autopilot_program = data.autopilot_program;
    if (!autopilot_program) {
        throw new CommandValidationError("invalid program");
    }
    if(programs.indexOf(autopilot_program) == -1) {
        throw new CommandValidationError("invalid program");
    }
    return { autopilot_program };
}

const validateRunAutopilotHeadingToWaypoint = (data) => {
    const waypointUUID = data.waypoint_uuid
    if(!waypointUUID) {
        throw new CommandValidationError("waypoint_uuid required");
    }
    const waypointType = data.waypoint_type
    if(!waypointType) {
        throw new CommandValidationError("waypoint_type required");
    }
    if (waypointType !== "ore" && waypointType !== "station") {
        throw new CommandValidationError("invalid waypoint_type");
    }
    return {
        waypointType,
        waypointUUID,
    }
}

const validateStartCoreUpgrade = (data) => {
    // Also validated cancel_core_upgrade
    const slug = data.slug
    if (!slug) {
        throw new CommandValidationError("slug is required");
    }
    if (
        slug !== "advanced_electronics"
        && slug !== "titanium_alloy_hull"
        && slug !== "liquid_nitrogen_cooling"
    ) {
        throw new CommandValidationError("invalid slug");
    }
    return slug;
}

const validateStartShipUpgrade = (data) => {
    // Also validated cancel_ship_upgrade
    const slug = data.slug;
    if (!slug) {
        throw new CommandValidationError("slug is required");
    }
    const upgrades = [
        'scanner_range',
        'radar_sensitivity',
        'anti_radar_coating',
        'scanner_lock_traversal',
        'engine_newtons',
        'ore_capacity',
        'apu_efficiency',
        'fuel_capacity',
        'battery_capacity',

    ];
    if (upgrades.indexOf(slug) === -1) {
        throw new CommandValidationError("invalid slug");
    }
    return slug;
}

const validateLaunchTubeWeapon = (data) => {
    const launchVelocity = data.launch_velocity
    if(!launchVelocity) {
        throw new CommandValidationError("launchVelocity required");
    }
    let _lv;
    try {
        _lv = parseInt(launchVelocity)
    } catch(e) {
        throw new CommandValidationError("invalid launchVelocity");
    }
    if(isNaN(_lv)) {
        throw new CommandValidationError("invalid launchVelocity");
    }
    if(_lv < 1 || _lv > 1000) {
        throw new CommandValidationError("invalid launchVelocity");
    }
    return _lv
}

exports.validateSetHeadingCommand = validateSetHeadingCommand;
exports.validateSetScannerLockTargetCommand = validateSetScannerLockTargetCommand;
exports.validateRunAutoPilotProgram = validateRunAutoPilotProgram;
exports.validateRunAutopilotHeadingToWaypoint = validateRunAutopilotHeadingToWaypoint;
exports.validateStartCoreUpgrade = validateStartCoreUpgrade;
exports.validateStartShipUpgrade = validateStartShipUpgrade;
exports.validateLaunchTubeWeapon = validateLaunchTubeWeapon;
