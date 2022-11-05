
from collections import OrderedDict
import random
from typing import Tuple, Dict, TypedDict, Optional, Generator, List, Union

from api.models.base import BaseModel
from api.models.ship_skin import ship_skins, DEFAULT_SKIN_SLUG
from api import utils2d
from api import constants
from .ship_upgrade import (
    get_upgrade_profile_1,
    UpgradeType,
    UpgradeCost,
    UpgradeSummary,
)


class ShipCommandError(Exception):
    pass

class AutopilotError(Exception):
    pass

class InsufficientPowerError(ShipCommandError):
    pass

class InsufficientFuelError(ShipCommandError):
    pass

class InsufficientOreError(ShipCommandError):
    pass


class MapFeatureType:
    ORE = "ore"
    SPACE_STATION = "station"

class ShipCoatType:
    NONE = None
    RADAR_DEFEATING = "radar_defeating"

class MapMiningLocationDetails(TypedDict):
    uuid: str
    name: Optional[str]
    position_meters_x: int
    position_meters_y: int
    service_radius_meters: int
    collision_radius_meters: int
    position_map_units_x: int # Perform map unit version up front
    position_map_units_y: int #
    service_radius_map_units: int #
    starting_ore_amount_kg: int

class MapSpaceStation(TypedDict):
    uuid: str
    name: Optional[str]
    position_meters_x: int
    position_meters_y: int
    service_radius_meters: int
    collision_radius_meters: int
    position_map_units_x: int # Perform map unit version up front
    position_map_units_y: int #
    service_radius_map_units: int #

class ShipCommands:
    LEAVE_GAME = 'leave_game'

    SET_HEADING = 'set_heading'

    ACTIVATE_ENGINE = 'activate_engine'
    DEACTIVATE_ENGINE = 'deactivate_engine'
    LIGHT_ENGINE = 'light_engine'
    UNLIGHT_ENGINE = 'unlight_engine'
    BOOST_ENGINE = 'boost_engine'

    ACTIVATE_APU = 'activate_apu'
    DEACTIVATE_APU = 'deactivate_apu'

    ACTIVATE_SCANNER = 'activate_scanner'
    DEACTIVATE_SCANNER = 'deactivate_scanner'
    SET_SCANNER_MODE_RADAR = 'set_scanner_mode_radar'
    SET_SCANNER_MODE_IR = 'set_scanner_mode_ir'
    SET_SCANNER_LOCK_TARGET = 'set_scanner_lock_target'

    RUN_AUTOPILOT_PROGRAM = 'run_autopilot'
    RUN_AUTOPILOT_HEADING_TO_WAYPOINT = "run_autopilot_heading_to_waypoint"
    DISABLE_AUTO_PILOT = 'disable_autopilot'

    CHARGE_EBEAM = 'charge_ebeam'
    PAUSE_CHARGE_EBEAM = 'pause_charge_ebeam'
    FIRE_EBEAM = 'fire_ebeam'

    EXTEND_GRAVITY_BRAKE = "extend_gravity_brake"
    RETRACT_GRAVITY_BRAKE = "retract_gravity_brake"
    START_ORE_MINING = 'start_ore_mining'
    STOP_ORE_MINING = 'stop_ore_mining'
    TRADE_ORE_FOR_ORE_COIN = 'trade_ore_for_ore_coin'

    START_FUELING = "start_fueling"
    STOP_FUELING = "stop_fueling"

    START_CORE_UPGRADE = "start_core_upgrade"
    START_SHIP_UPGRADE = "start_ship_upgrade"
    CANCEL_CORE_UPGRADE = "cancel_core_upgrade"
    CANCEL_SHIP_UPGRADE = "cancel_ship_upgrade"

    # Tube Weapons
    BUY_MAGNET_MINE = "buy_magnet_mine"
    LAUNCH_MAGNET_MINE = "launch_magnet_mine"
    BUY_EMP = "buy_emp"
    LAUNCH_EMP = "launch_emp"
    BUY_HUNTER_DRONE = "buy_hunter_drone"
    LAUNCH_HUNTER_DRONE = "launch_hunter_drone"

class ShipStateKey:
    MASS = 'mass'

class ShipDeathType:
    EXPLOSION = 'explosion'
    EXPLOSION_NEW = 'new_explosion'
    AFLAME = 'aflame'
    ADRIFT = 'adrift'

class ShipScannerMode:
    RADAR = 'radar'
    IR = 'ir'

class ScannedShipElement(TypedDict):
    id: str
    skin_slug: str
    designator: str
    anti_radar_coating_level: int
    scanner_thermal_signature: int
    coord_x: int
    coord_y: int
    visual_heading: int #heading of the scanned ship
    visual_map_nose_coord: Tuple[int]
    visual_map_bottom_left_coord: Tuple[int]
    visual_map_bottom_right_coord: Tuple[int]
    visual_map_bottom_center_coord: Tuple[int]
    relative_heading: int # Rounded int describing bearing to element
    target_heading: float # Float describing beaing to element
    velocity_x_meters_per_second: float
    velocity_y_meters_per_second: float
    distance: int
    alive: bool
    aflame: bool
    exploded: bool
    in_visual_range: bool
    visual_engine_lit: bool
    visual_ebeam_charging: bool
    visual_ebeam_charge_percent: float
    visual_ebeam_firing: bool
    visual_ebeam_color: str
    visual_engine_boosted_last_frame: int
    visual_gravity_brake_position: int
    visual_gravity_brake_deployed_position: int
    visual_gravity_brake_active: bool
    visual_mining_ore_location: Union[None, str]
    visual_fueling_at_station: bool
    visual_last_tube_fire_frame: Union[None, int]

class ScannedMagnetMineElement(TypedDict):
    id: str
    velocity_x_meters_per_second: float
    velocity_y_meters_per_second: float
    coord_x: int
    coord_y: int
    distance: int
    exploded: bool
    relative_heading: int
    percent_armed: float

class ScannedEMPElement(TypedDict):
    id: str
    coord_x: int
    coord_y: int
    distance: int
    exploded: bool
    relative_heading: int
    percent_armed: float

class TimerItem(TypedDict):
    name: str
    percent: int
    slug: Optional[str]


class AutoPilotPrograms:
    POSITION_HOLD = 'position_hold'
    HEADING_LOCK_ON_TARGET = 'lock_target'
    HEADING_LOCK_PROGRADE = 'lock_prograde'
    HEADING_LOCK_RETROGRADE = 'lock_retrograde'
    HEADING_LOCK_WAYPOINT = 'lock_waypoint'


class Ship(BaseModel):
    def __init__(self):
        super().__init__()

        self.skin_slug = None

        self.map_units_per_meter = None

        self.team_id = None

        # x,y coords for the center of the ship.
        # These coords show where on the map the ship is
        self.coord_x = 0
        self.coord_y = 0

        # heading of ship in degrees (between 0 and 359)
        self.heading = 0

        # <START OF RELATIVE COORDINATES>
        # These are the coordinates for the ship if the ship's center is at the origin: (coord_x, coord_y) == (0, 0,)
        # Relative rotated hitbox coordinates
        # these values are rotated to account for ship heading.
        self.rel_rot_coord_hitbox_nose = (None, None, )
        self.rel_rot_coord_hitbox_bottom_left = (None, None, )
        self.rel_rot_coord_hitbox_bottom_right = (None, None, )
        self.rel_rot_coord_hitbox_bottom_center = (None, None, )
        # relative hitbox coordinates
        # of the ship with heading fixed to zero.
        # These coords will NOT change
        self.rel_fixed_coord_hitbox_nose = (None, None, )
        self.rel_fixed_coord_hitbox_bottom_left = (None, None, )
        self.rel_fixed_coord_hitbox_bottom_right = (None, None, )
        self.rel_fixed_coord_hitbox_bottom_center = (None, None, )
        # </END OF RELATIVE COORDINATES>

        # Velocity
        self.velocity_x_meters_per_second = float(0)
        self.velocity_y_meters_per_second = float(0)

        self._upgrades = None
        # Internal bookkeeping data to track
        # actively researching upgrades.
        # Data is being duplicated for performace.
        self._ship_upgrade_active_indexes: List[int] = []
        self._core_upgrade_active_indexes: List[int] = []
        # External data that is sent to the front end.
        self._upgrade_summary: Dict[str, Dict[str, UpgradeSummary]] = {}

        self.visual_range = None

        # Battery
        self.battery_power = 0
        self.battery_capacity = 0
        self.battery_mass = 0

        # Fuel Tank
        self.fuel_level = 0
        self.fuel_capacity = 0
        self.fueling_at_station = False
        self.fuel_cost_ore_kg_per_fuel_unit = None
        self.refueling_rate_fuel_units_per_second = None

        # Engine
        self.engine_mass = 0
        self.engine_newtons = 0
        self.engine_lit = False
        self.engine_online = False
        self.engine_boosting = False
        self.engine_boosted = False
        self.engine_boosted_last_frame = -10
        self.engine_boost_multiple = None
        self.engine_starting = False
        self.engine_startup_power_used = None
        self.engine_idle_power_requirement_per_second = None
        self.engine_seconds_to_activate = None
        self.engine_activation_power_required_total = None
        self.engine_activation_power_required_per_second = None
        self.engine_fuel_usage_per_second = None
        self.engine_battery_charge_per_second = None
        self.engine_lit_thermal_signature_rate_per_second = None

        # APU
        self.apu_starting = False
        self.apu_startup_power_used = None
        self.apu_online = False
        self.apu_seconds_to_activate = None
        self.apu_activation_power_required_total = None
        self.apu_activation_power_required_per_second = None
        self.apu_online_thermal_signature_rate_per_second = None
        self.apu_fuel_usage_per_second = None
        self.apu_battery_charge_per_second = None

        # Scanner
        self.scanner_designator = None # A unique "human readable" identifier used to identify this ship on other ships' scanners
        self.scanner_online = False
        self.scanner_starting = False
        self.scanner_mode = None
        self.scanner_radar_range = None
        self.scanner_ir_range = None
        self.scanner_ir_minimum_thermal_signature = None
        self.scanner_radar_sensitivity = None
        self.scanner_idle_power_requirement_per_second = None
        self.scanner_activation_power_required_total = None
        self.scanner_activation_power_required_per_second = None
        self.scanner_startup_power_used = None
        self.scanner_seconds_to_activate = None
        self.scanner_locked = False
        self.scanner_locking = False
        self.scanner_locking_power_used = None
        self.scanner_lock_target = None
        self.scanner_get_lock_power_requirement_total = None
        self.scanner_get_lock_power_requirement_per_second = None
        self.scanner_ship_data: Dict[str, ScannedShipElement] = OrderedDict()
        self.scanner_magnet_mine_data: Dict[str, ScannedMagnetMineElement] = OrderedDict()
        self.scanner_emp_data: Dict[str, ScannedEMPElement] = OrderedDict()
        # Temperature of the ship as it appears on an other ships' IR mode scanner
        self.scanner_thermal_signature = None
        self.anti_radar_coating_level = None

        self.scanner_thermal_signature_dissipation_per_second = None

        self.scanner_locking_max_traversal_degrees = None
        self.scanner_locked_max_traversal_degrees = None
        self.scanner_lock_traversal_degrees_previous_frame = None
        self.scanner_lock_traversal_slack = None

        # Ship Energy Beam
        self.ebeam_charge_rate_per_second = None
        self.ebeam_charge_power_usage_per_second = None
        self.ebeam_charge_thermal_signature_rate_per_second = None
        self.ebeam_charge = None
        self.ebeam_charge_capacity = None
        self.ebeam_charging = False
        self.ebeam_firing = False
        self.ebeam_discharge_rate_per_second = None
        self.ebeam_charge_fire_minimum = None
        self.ebeam_color = None
        self.ebeam_last_hit_frame = None

        # Special weapons tubes
        self.special_weapons_tubes_count = None
        self.last_tube_fire_frame = None
        self._special_weapon_costs = None
        self._special_weapons_min_launch_velocity = None
        self._special_weapons_max_launch_velocity = None
        self._special_weapons_launch_velocity = None
        self.magnet_mines_loaded = 5
        self.emps_loaded = 5
        self.hunter_drones_loaded = 5
        self.magnet_mine_firing = False
        self.emp_firing = False
        self.hunter_drone_firing = False

        self.autopilot_program = None
        self.autopilot_waypoint_uuid = None
        self.autopilot_waypoint_type = None

        # Damage
        self.died_on_frame = None
        self.aflame_since_frame = None
        self._seconds_to_aflame = random.randint(0, 1)
        self.explode_immediately = random.randint(0, 9) == 1
        self.exploded = False
        self._removed_from_map = False
        self._seconds_to_explode = random.randint(3, 6)

        # Space station interactions
        self.docked_at_station = None
        self.docking_at_station = None
        self.gravity_brake_position = 0
        self.gravity_brake_deployed_position = 100
        self.gravity_brake_traversal_per_second = None
        self.gravity_brake_retracting = False
        self.gravity_brake_extending = False
        self.gravity_brake_active = False # flipped to true, the ship rapidly slows down.
        self.scouted_station_gravity_brake_catches_last_frame: Dict[str, int] = {}

        # Mining interactions
        self.parked_at_ore_mine = None
        self.cargo_ore_mass_capacity_kg = None
        self.cargo_ore_mass_kg = 0.0
        self.virtual_ore_kg = 100_000
        self.mining_ore = False
        self.mining_ore_power_usage_per_second = None
        self.mining_ore_kg_collected_per_second = None
        self.scouted_mine_ore_remaining: Dict[str, float] = {}
        self.last_ore_deposit_frame = None

        # cached map data
        self._ore_mines: Dict[str, MapMiningLocationDetails] = {}
        self._space_stations: Dict[str, MapSpaceStation] = {}

        # Arbitrary ship state data
        self._state = {}

    @property
    def coords(self) -> Tuple[int]:
        return (self.coord_x, self.coord_y,)

    @property
    def map_nose_coord(self) -> Tuple:
        return (
            self.coord_x + self.rel_rot_coord_hitbox_nose[0],
            self.coord_y + self.rel_rot_coord_hitbox_nose[1],
        )

    @property
    def map_bottom_left_coord(self) -> Tuple:
        return (
            self.coord_x + self.rel_rot_coord_hitbox_bottom_left[0],
            self.coord_y + self.rel_rot_coord_hitbox_bottom_left[1],
        )

    @property
    def map_bottom_right_coord(self) -> Tuple:
        return (
            self.coord_x + self.rel_rot_coord_hitbox_bottom_right[0],
            self.coord_y + self.rel_rot_coord_hitbox_bottom_right[1],
        )

    @property
    def map_bottom_center_coord(self) -> Tuple:
        return (
            self.coord_x + self.rel_rot_coord_hitbox_bottom_center[0],
            self.coord_y + self.rel_rot_coord_hitbox_bottom_center[1],
        )

    @property
    def ebeam_heading(self) -> Union[float, int]:
        if self.scanner_lock_target and self.scanner_locked and self.autopilot_program == AutoPilotPrograms.HEADING_LOCK_ON_TARGET:
            return self.scanner_ship_data[self.scanner_lock_target]['target_heading']
        return self.heading


    @property
    def hitbox_lines(self) -> Tuple[Tuple[Tuple]]:
        return (
            (self.map_nose_coord, self.map_bottom_left_coord),
            (self.map_bottom_left_coord, self.map_bottom_center_coord),
            (self.map_bottom_center_coord, self.map_bottom_right_coord),
            (self.map_bottom_right_coord, self.map_nose_coord),
        )

    @property
    def mass(self) -> int:
        return self._state.get(ShipStateKey.MASS, (
            self.battery_mass
            + self.engine_mass
            + self.cargo_ore_mass_kg
            + int(self.fuel_level / constants.FUEL_UNITS_PER_KG)
            + constants.HULL_BASE_MASS
            + constants.PILOT_MASS
        ))

    @property
    def is_stationary(self) -> bool:
        return self.velocity_x_meters_per_second == 0 and self.velocity_y_meters_per_second == 0

    @property
    def engine_heading(self) -> int:
        return (self.heading - 180) if self.heading >= 180 else (self.heading + 180)

    @property
    def scanner_range(self):
        return self.scanner_radar_range if self.scanner_mode == ShipScannerMode.RADAR else self.scanner_ir_range

    @property
    def current_FOW_vision(self):
        return self.scanner_range if self.scanner_online else self.visual_range

    @property
    def gravity_brake_deployed(self) -> bool:
        return self.gravity_brake_position == self.gravity_brake_deployed_position

    @property
    def special_weapons_loaded(self) -> int:
        # Total tube weapons aboard.
        return (
            self.magnet_mines_loaded
            + self.emps_loaded
            + self.hunter_drones_loaded
        )

    def to_dict(self) -> Dict:
        """ Get JSON serializable representation of the ship.
            this is all seen by the user in the SPA via ApiService::frameData.ship
        """
        return {
            'id': self.id,
            'team_id': self.team_id,
            'skin_slug': self.skin_slug,
            'mass': self.mass,
            'coord_x': self.coord_x,
            'coord_y': self.coord_y,
            'heading': self.heading,
            'velocity_x_meters_per_second': self.velocity_x_meters_per_second,
            'velocity_y_meters_per_second': self.velocity_y_meters_per_second,
            'battery_power': self.battery_power,
            'battery_capacity': self.battery_capacity,
            'fuel_level': self.fuel_level,
            'fuel_capacity': self.fuel_capacity,
            'fueling_at_station': self.fueling_at_station,
            'fuel_cost_ore_kg_per_fuel_unit': self.fuel_cost_ore_kg_per_fuel_unit,

            'map_nose_coord': self.map_nose_coord,
            'map_bottom_left_coord': self.map_bottom_left_coord,
            'map_bottom_right_coord': self.map_bottom_right_coord,
            'map_bottom_center_coord': self.map_bottom_center_coord,

            'upgrade_summary': self._upgrade_summary,

            'engine_newtons': self.engine_newtons,
            'engine_online': self.engine_online,
            'engine_lit': self.engine_lit,
            'engine_starting': self.engine_starting,
            'engine_boosted': self.engine_boosted,
            'engine_boosted_last_frame': self.engine_boosted_last_frame,
            'engine_lit_thermal_signature_rate_per_second': self.engine_lit_thermal_signature_rate_per_second,

            'apu_starting': self.apu_starting,
            'apu_online': self.apu_online,
            'apu_battery_charge_per_second': self.apu_battery_charge_per_second,
            'apu_fuel_usage_per_second': self.apu_fuel_usage_per_second,
            'apu_online_thermal_signature_rate_per_second': self.apu_online_thermal_signature_rate_per_second,

            'scanner_online': self.scanner_online,
            'scanner_locking': self.scanner_locking,
            'scanner_locked': self.scanner_locked,
            'scanner_lock_target': self.scanner_lock_target,
            'scanner_starting': self.scanner_starting,
            'scanner_mode': self.scanner_mode,
            'scanner_radar_range': self.scanner_radar_range,
            'scanner_ir_range': self.scanner_ir_range,
            'scanner_ir_minimum_thermal_signature': self.scanner_ir_minimum_thermal_signature,
            'scanner_ship_data': list(self.scanner_ship_data.values()),
            'scanner_magnet_mine_data': list(self.scanner_magnet_mine_data.values()),
            'scanner_emp_data': list(self.scanner_emp_data.values()),
            'scanner_thermal_signature': self.scanner_thermal_signature,
            'scanner_lock_traversal_slack': self.scanner_lock_traversal_slack,
            'scanner_locking_max_traversal_degrees': self.scanner_locking_max_traversal_degrees,
            'scanner_locked_max_traversal_degrees': self.scanner_locked_max_traversal_degrees,
            'scanner_radar_sensitivity': self.scanner_radar_sensitivity,
            'anti_radar_coating_level': self.anti_radar_coating_level,

            'ebeam_firing': self.ebeam_firing,
            'ebeam_charging': self.ebeam_charging,
            'ebeam_charge_capacity': self.ebeam_charge_capacity,
            'ebeam_color': self.ebeam_color,
            'ebeam_charge': self.ebeam_charge,
            'ebeam_can_fire': self.ebeam_charge >= self.ebeam_charge_fire_minimum and not self.ebeam_firing,
            'ebeam_last_hit_frame': self.ebeam_last_hit_frame,
            'ebeam_charge_rate_per_second': self.ebeam_charge_rate_per_second,
            'ebeam_charge_power_usage_per_second': self.ebeam_charge_power_usage_per_second,
            'ebeam_charge_thermal_signature_rate_per_second': self.ebeam_charge_thermal_signature_rate_per_second,
            'ebeam_charge_fire_minimum': self.ebeam_charge_fire_minimum,

            'special_weapons_tubes_count': self.special_weapons_tubes_count,
            'last_tube_fire_frame': self.last_tube_fire_frame,
            'special_weapons_loaded': self.special_weapons_loaded,
            'magnet_mines_loaded': self.magnet_mines_loaded,
            'emps_loaded': self.emps_loaded,
            'hunter_drones_loaded': self.hunter_drones_loaded,

            'docked_at_station': self.docked_at_station,
            'scouted_station_gravity_brake_catches_last_frame': self.scouted_station_gravity_brake_catches_last_frame,
            'gravity_brake_position': self.gravity_brake_position,
            'gravity_brake_deployed_position': self.gravity_brake_deployed_position,
            'gravity_brake_retracting': self.gravity_brake_retracting,
            'gravity_brake_extending': self.gravity_brake_extending,
            'gravity_brake_active': self.gravity_brake_active,
            'gravity_brake_deployed': self.gravity_brake_deployed,

            'parked_at_ore_mine': self.parked_at_ore_mine,
            'mining_ore': self.mining_ore,
            'cargo_ore_mass_kg': self.cargo_ore_mass_kg,
            'cargo_ore_mass_capacity_kg': self.cargo_ore_mass_capacity_kg,
            'virtual_ore_kg': self.virtual_ore_kg,
            'scouted_mine_ore_remaining': self.scouted_mine_ore_remaining,
            'last_ore_deposit_frame': self.last_ore_deposit_frame,

            'alive': self.died_on_frame is None,
            'died_on_frame': self.died_on_frame,
            'aflame': self.aflame_since_frame is not None,
            'exploded': self.exploded,

            'visual_range': self.visual_range,

            'autopilot_program': self.autopilot_program,

            'timers': list(self.get_timer_items()),
        }

    @classmethod
    def spawn(
        cls,
        team_id: str,
        special_weapon_costs: Dict[str, int],
        map_units_per_meter: int = 1,
        skin_slug: str = None,
    ) -> "Ship":
        """ Create new unpositioned ship with defaults
        """
        instance = cls()

        instance.skin_slug = DEFAULT_SKIN_SLUG if skin_slug is None else skin_slug
        if instance.skin_slug not in ship_skins:
            raise Exception("invalid ship skin slug")

        instance.map_units_per_meter = map_units_per_meter
        instance.team_id = team_id

        instance._upgrades = get_upgrade_profile_1()
        instance._special_weapon_costs = special_weapon_costs
        instance._upgrade_summary[UpgradeType.CORE] = {}
        for cu in instance._upgrades[UpgradeType.CORE]:
            instance._upgrade_summary[UpgradeType.CORE][cu.slug] = {
                "name": cu.name,
                "current_level": 0,
                "max_level": 1,
                "seconds_researched": None,
                "current_cost": cu.cost,
            }
        instance._upgrade_summary[UpgradeType.SHIP] = {}
        for su in instance._upgrades[UpgradeType.SHIP]:
            instance._upgrade_summary[UpgradeType.SHIP][su.slug] = {
                "name": su.name,
                "current_level": 0,
                "max_level": su.max_level,
                "seconds_researched": None,
                "current_cost": su.cost_progression[1],
            }

        # Orient hit boxes
        x_len = constants.SHIP_X_LEN * map_units_per_meter
        y_len = constants.SHIP_Y_LEN * map_units_per_meter
        # Ship Nose
        nose_x = 0
        nose_y = round(y_len / 2)
        instance.rel_rot_coord_hitbox_nose = (nose_x, nose_y, )
        instance.rel_fixed_coord_hitbox_nose = (nose_x, nose_y, )
        # Bottom Left Corner
        bottom_left_x = round((x_len / 2) * -1)
        bottom_y = round(((y_len / 2) * -1) + (y_len / 8))
        instance.rel_rot_coord_hitbox_bottom_left = (bottom_left_x, bottom_y, )
        instance.rel_fixed_coord_hitbox_bottom_left = (bottom_left_x, bottom_y, )
        # Bottom Right Corner
        bottom_right_x = round(x_len / 2)
        bottom_right_y = bottom_y
        instance.rel_rot_coord_hitbox_bottom_right = (bottom_right_x, bottom_right_y, )
        instance.rel_fixed_coord_hitbox_bottom_right = (bottom_right_x, bottom_right_y, )
        # Bottom Center
        bottom_center_x = 0
        bottom_center_y = nose_y * -1
        instance.rel_rot_coord_hitbox_bottom_center = (bottom_center_x, bottom_center_y, )
        instance.rel_fixed_coord_hitbox_bottom_center = (bottom_center_x, bottom_center_y, )


        instance.battery_power = constants.BATTERY_STARTING_POWER
        instance.battery_capacity = constants.BATTERY_POWER_CAPACITY
        instance.battery_mass = constants.BATTERY_MASS

        instance.fuel_level = constants.FUEL_START_LEVEL
        instance.fuel_capacity = constants.FUEL_CAPACITY
        instance.fuel_cost_ore_kg_per_fuel_unit = constants.FUEL_COST_ORE_KG_PER_FUEL_UNIT
        instance.refueling_rate_fuel_units_per_second = constants.REFUELING_RATE_FUEL_UNITS_PER_SECOND

        instance.visual_range = constants.MAX_VISUAL_RANGE_M

        instance.engine_mass = constants.ENGINE_MASS
        instance.engine_newtons = constants.ENGINE_BASE_FORCE_N
        instance.engine_seconds_to_activate = constants.SECONDS_TO_START_ENGINE
        instance.engine_activation_power_required_total = constants.ACTIVATE_ENGINE_POWER_REQUIREMENT_TOTAL
        instance.engine_activation_power_required_per_second = constants.ACTIVATE_ENGINE_POWER_REQUIREMENT_PER_SECOND
        instance.engine_idle_power_requirement_per_second = constants.ENGINE_IDLE_POWER_REQUIREMENT_PER_SECOND
        instance.engine_fuel_usage_per_second = constants.ENGINE_FUEL_USAGE_PER_SECOND
        instance.engine_battery_charge_per_second = constants.ENGINE_BATTERY_CHARGE_PER_SECOND
        instance.engine_lit_thermal_signature_rate_per_second = constants.ENGINE_LIT_THERMAL_SIGNATURE_RATE_PER_SECOND
        instance.engine_boost_multiple = constants.ENGINE_BOOST_MULTIPLE

        instance.apu_seconds_to_activate = constants.APU_SECONDS_TO_START
        instance.apu_activation_power_required_total = constants.ACTIVATE_APU_POWER_REQUIREMENT_TOTAL
        instance.apu_activation_power_required_per_second = constants.ACTIVATE_APU_POWER_REQUIREMENT_PER_SECOND
        instance.apu_online_thermal_signature_rate_per_second = constants.APU_ONLINE_THERMAL_SIGNATURE_RATE_PER_SECOND
        instance.apu_battery_charge_per_second = constants.APU_BATTERY_CHARGE_PER_SECOND
        instance.apu_fuel_usage_per_second = constants.ENGINE_FUEL_USAGE_PER_SECOND

        instance.scanner_mode = ShipScannerMode.RADAR
        instance.scanner_radar_range = constants.SCANNER_MODE_RADAR_RANGE_M
        instance.scanner_ir_range = constants.SCANNER_MODE_IR_RANGE_M
        instance.scanner_ir_minimum_thermal_signature = constants.SCANNER_IR_MINIMUM_THERMAL_SIGNATURE
        instance.scanner_radar_sensitivity = 0
        instance.scanner_idle_power_requirement_per_second = constants.SCANNER_POWER_REQUIREMENT_PER_SECOND
        instance.scanner_seconds_to_activate = constants.SCANNER_SECONDS_TO_START
        instance.scanner_activation_power_required_total = constants.ACTIVATE_SCANNER_POWER_REQUIREMENT_TOTAL
        instance.scanner_activation_power_required_per_second = constants.ACTIVATE_SCANNER_POWER_REQUIREMENT_PER_SECOND
        instance.scanner_get_lock_power_requirement_total = constants.SCANNER_GET_LOCK_POWER_REQUIREMENT_TOTAL
        instance.scanner_get_lock_power_requirement_per_second = constants.SCANNER_GET_LOCK_POWER_REQUIREMENT_PER_SECOND
        instance.scanner_thermal_signature = 0
        instance.anti_radar_coating_level = 0

        instance.scanner_thermal_signature_dissipation_per_second = constants.THERMAL_DISSIPATION_PER_SECOND

        instance.scanner_locking_max_traversal_degrees = constants.SCANNER_LOCKING_MAX_TRAVERSAL_DEGREES
        instance.scanner_locked_max_traversal_degrees = constants.SCANNER_LOCKED_MAX_TRAVERSAL_DEGREES

        instance.ebeam_charge_rate_per_second = constants.EBEAM_CHARGE_RATE_PER_SECOND
        instance.ebeam_charge_power_usage_per_second = constants.EBEAM_CHARGE_POWER_USAGE_PER_SECOND
        instance.ebeam_charge_thermal_signature_rate_per_second = constants.EBEAM_CHARGE_THERMAL_SIGNATURE_RATE_PER_SECOND
        instance.ebeam_charge = 0
        instance.ebeam_charge_capacity = constants.EBEAM_CHARGE_CAPACITY
        instance.ebeam_discharge_rate_per_second = constants.EBEAM_DISCHARGE_RATE_PER_SECOND
        instance.ebeam_charge_fire_minimum = constants.EBEAM_CHARGE_FIRE_MINIMUM
        instance.ebeam_color = constants.EBEAM_COLOR_STARTING

        instance.special_weapons_tubes_count = constants.SPECIAL_WEAPONS_TUBES_COUNT
        instance._special_weapons_min_launch_velocity = constants.SPECIAL_WEAPONS_MIN_LAUNCH_VELOCITY
        instance._special_weapons_max_launch_velocity = constants.SPECIAL_WEAPONS_MAX_LAUNCH_VELOCITY
        instance._special_weapons_launch_velocity = round(
            (
                instance._special_weapons_min_launch_velocity
                + instance._special_weapons_max_launch_velocity
            ) / 2
        )

        instance.cargo_ore_mass_capacity_kg = constants.ORE_CAPACITY_KG
        instance.mining_ore_power_usage_per_second = constants.MINING_ORE_POWER_USAGE_PER_SECOND
        instance.mining_ore_kg_collected_per_second = constants.MINING_ORE_KG_COLLECTED_PER_SECOND

        instance.gravity_brake_traversal_per_second = constants.GRAVITY_BRAKE_TRAVERSAL_PER_SECOND

        return instance


    def get_timer_items(self) -> Generator[TimerItem, None, None]:
        if self.engine_starting:
            yield {
                'name': 'Engine',
                'percent': round(
                    self.engine_startup_power_used / self.engine_activation_power_required_total * 100
                ),
            }
        if self.scanner_starting:
            yield {
                'name': 'Scanner',
                'slug': 'scanner_startup',
                'percent': round(
                    self.scanner_startup_power_used / self.scanner_activation_power_required_total * 100
                ),
            }
        if self.scanner_locking:
            yield {
                'name': 'Locking',
                'slug': 'scanner_locking',
                'percent': round(
                    self.scanner_locking_power_used / self.scanner_get_lock_power_requirement_total * 100
                ),
            }
        if self.ebeam_charge > 0:
            yield {
                'name': 'EME-Beam',
                'percent': round(
                    self.ebeam_charge / self.ebeam_charge_capacity * 100
                ),
            }
        if self.apu_starting:
            yield {
                'name': 'aux power',
                'percent': round(
                    self.apu_startup_power_used / self.apu_activation_power_required_total * 100
                ),
            }

        if self.gravity_brake_extending:
            yield {
                'name': 'Brake',
                'percent': round(
                    self.gravity_brake_position / self.gravity_brake_deployed_position * 100
                ),
            }
        elif self.gravity_brake_retracting:
            yield {
                'name': 'Brake',
                'percent': round( # count down timer (starts filled, and empties)
                    self.gravity_brake_position / self.gravity_brake_deployed_position * 100
                ),
            }


    def use_battery_power(self, quantity: float) -> None:
        if quantity > self.battery_power:
            raise InsufficientPowerError
        self.battery_power -= quantity

    def charge_battery(self, quantity: int) -> None:
        self.battery_power = min(
            self.battery_capacity,
            self.battery_power + quantity,
        )

    def use_fuel(self, quantity: float) -> None:
        if quantity > self.fuel_level:
            raise InsufficientFuelError
        self.fuel_level -= quantity

    def add_fuel(self, quantity: float) -> None:
        self.fuel_level += min(
            self.fuel_capacity - self.fuel_level,
            quantity,
        )

    def withdraw_ore(self, quantity: float):
        if quantity > (self.cargo_ore_mass_kg + self.virtual_ore_kg):
            raise InsufficientOreError

        # withdraw from physical ore first
        pool = 0
        if self.cargo_ore_mass_kg > 0:
            adj = min(self.cargo_ore_mass_kg, quantity)
            self.cargo_ore_mass_kg -= adj
            pool += adj

        # withdraw from virtual ore after
        if pool < quantity:
            self.virtual_ore_kg -= (quantity - pool)


    def adjust_resources(self, fps: int, game_frame: int):

        ''' ENERGY BEAM '''
        if self.ebeam_charging:
            battery_adj = self.ebeam_charge_power_usage_per_second / fps
            try:
                self.use_battery_power(battery_adj)
            except InsufficientPowerError:
                self.ebeam_charging = False
            else:
                charge_adj = self.ebeam_charge_rate_per_second / fps
                self.ebeam_charge = min(
                    self.ebeam_charge + charge_adj,
                    self.ebeam_charge_capacity,
                )
            if self.ebeam_charge >= self.ebeam_charge_capacity:
                self.ebeam_charging = False

        ''' Mining '''
        if self.mining_ore:
            adj = self.mining_ore_power_usage_per_second / fps
            try:
                self.use_battery_power(adj)
            except InsufficientPowerError:
                self.mining_ore = False

        ''' REFUELING '''
        if self.fueling_at_station:
            room_in_tank = self.fuel_capacity - self.fuel_level
            if (
                not self.docked_at_station
                or not self.gravity_brake_deployed
                or not self.is_stationary
                or room_in_tank <= 0
            ):
                self.fueling_at_station = False
            else:
                fuel_adj = min(room_in_tank, self.refueling_rate_fuel_units_per_second / fps)
                ore_adj = self.fuel_cost_ore_kg_per_fuel_unit * fuel_adj
                try:
                    self.withdraw_ore(ore_adj)
                except InsufficientOreError:
                    self.fueling_at_station = False
                else:
                    self.add_fuel(fuel_adj)

        ''' Scanner POWER DRAW (RUNNING) '''
        if self.scanner_online:
            try:
                self.use_battery_power(self.scanner_idle_power_requirement_per_second / fps)
            except InsufficientPowerError:
                self.scanner_online = False
                self.scanner_locking = False
                self.scanner_lock_target = None
                self.scanner_locked = False
                self.scanner_lock_traversal_degrees_previous_frame = None
                self.scanner_lock_traversal_slack = None

            else:
                if self.scanner_locking:
                    lock_complete = self.scanner_locking_power_used >= self.scanner_get_lock_power_requirement_total
                    if lock_complete:
                        self.scanner_locked = True
                        self.scanner_locking = False
                        self.scanner_locking_power_used = None

                    else:
                        adj = min(
                            self.scanner_get_lock_power_requirement_per_second / fps,
                            self.scanner_get_lock_power_requirement_total - self.scanner_locking_power_used
                        )
                        try:
                            self.use_battery_power(adj)
                        except InsufficientPowerError:
                            self.scanner_locking = False
                            self.scanner_lock_target = None
                            self.scanner_locking_power_used = None
                            self.scanner_lock_traversal_degrees_previous_frame = None
                            self.scanner_lock_traversal_slack = None
                        else:
                            self.scanner_locking_power_used += adj


        elif self.scanner_starting:
            ''' Scanner POWER DRAW (STARTING) '''
            startup_complete = self.scanner_startup_power_used >= self.scanner_activation_power_required_total
            if startup_complete:
                self.scanner_starting = False
                self.scanner_startup_power_used = None
                try:
                    self.use_battery_power(
                        self.scanner_idle_power_requirement_per_second / fps
                    )
                except InsufficientPowerError:
                    # Scanner startup complete but not enough power to idle scanner
                    pass
                else:
                    # Scanner Startup successful.
                    self.scanner_online = True

            else:
                # continue scanner startup
                adj = min(
                    self.scanner_activation_power_required_per_second / fps,
                    self.scanner_activation_power_required_total - self.scanner_startup_power_used,
                )
                try:
                    self.use_battery_power(adj)
                except InsufficientPowerError:
                    # Cancel startup, not enough power.
                    self.scanner_starting = False
                    self.scanner_startup_power_used = None
                else:
                    self.scanner_startup_power_used += adj



        ''' ENGINE POWER DRAW (STARTING) # # # '''
        self.engine_boosted = False
        if self.engine_starting:
            startup_complete = self.engine_startup_power_used >= self.engine_activation_power_required_total
            if startup_complete:
                self.engine_starting = False
                self.engine_startup_power_used = None
                try:
                    self.use_battery_power(
                        self.engine_idle_power_requirement_per_second / fps
                    )
                except InsufficientPowerError:
                    # Engine startup complete but not enough power to idle engine.
                    pass
                else:
                    # Engine Startup successful.
                    self.engine_online = True
            else:
                # Continue engine startup.
                adj = min(
                    self.engine_activation_power_required_per_second / fps,
                    self.engine_activation_power_required_total - self.engine_startup_power_used,
                )
                try:
                    self.use_battery_power(adj)
                except InsufficientPowerError:
                    # Cancel startup, not enough power.
                    self.engine_starting = False
                    self.engine_startup_power_used = None
                else:
                    self.engine_startup_power_used += adj

        elif self.engine_online and not self.engine_lit:
            ''' ENGINE POWER DRAW (IDLE) '''
            try:
                self.use_battery_power(
                    self.engine_idle_power_requirement_per_second / fps
                )
            except InsufficientPowerError:
                self.engine_online = False

        elif self.engine_lit:
            ''' ENGINE POWER GENERATION & FUEL CONSUMPTION (LIT) '''
            try:
                self.use_fuel(
                    self.engine_fuel_usage_per_second / fps
                )
            except InsufficientFuelError:
                # Flame out.
                self.engine_lit = False
                self.engine_online = False
                self.engine_boosting = False
            else:
                self.charge_battery(
                    self.engine_battery_charge_per_second / fps
                )

            if self.engine_boosting:
                self.engine_boosting = False
                try:
                    self.use_fuel(
                        self.engine_fuel_usage_per_second / fps * self.engine_boost_multiple
                    )

                except InsufficientFuelError:
                    # Flame out.
                    self.engine_lit = False
                    self.engine_online = False
                    self.engine_boosted = False

                else:
                    self.engine_boosted = True
                    self.engine_boosted_last_frame = game_frame

        # Auxiliary Power Unit
        if self.apu_starting:
            apu_startup_complete = self.apu_startup_power_used >= self.apu_activation_power_required_total
            if apu_startup_complete:
                self.apu_starting = False
                self.apu_online = True
            else:
                # FIXME: this can potentially draw slightly too much power on startup.
                adj = self.apu_activation_power_required_per_second / fps
                try:
                    self.use_battery_power(adj)
                except InsufficientPowerError:
                    self.apu_starting = False
                else:
                    self.apu_startup_power_used += adj

        elif self.apu_online:
            try:
                self.use_fuel(
                    self.apu_fuel_usage_per_second / fps
                )
            except InsufficientFuelError:
                self.apu_online = False
            else:
                self.charge_battery(
                    max(
                        round(self.apu_battery_charge_per_second / fps),
                        1,
                    )
                )

    def calculate_physics(self, fps: int) -> None:
        ## apply gravity brake
        if self.gravity_brake_active:
            if self.velocity_x_meters_per_second != 0:
                magX = abs(self.velocity_x_meters_per_second)
                if magX > 150:
                     # If more than 150M/S immediatly drop to 100M/S
                    delta = magX - 100
                else:
                    # reduce X by half 6 times per second.
                    delta = min(
                        magX,
                        max(5, magX / 2 / (fps / 6))
                    )
                direction = 1 if self.velocity_x_meters_per_second < 0 else -1
                self.velocity_x_meters_per_second += delta * direction
                if abs(self.velocity_x_meters_per_second) < 5:
                    self.velocity_x_meters_per_second = 0


            if self.velocity_y_meters_per_second != 0:
                magY = abs(self.velocity_y_meters_per_second)
                if magY > 150:
                    # If more than 150M/S immediatly drop to 100M/S
                    delta = magY - 100
                else:
                    # Otherwise reduce Y by half 6 times per second.
                    delta = min(
                        magY,
                        max(5, magY / 2 / (fps / 6))
                    )
                direction = 1 if self.velocity_y_meters_per_second < 0 else -1
                self.velocity_y_meters_per_second += delta * direction
                if abs(self.velocity_y_meters_per_second) < 5:
                    self.velocity_y_meters_per_second = 0

            if self.is_stationary:
                self.gravity_brake_active = False
                self.docked_at_station = self.docking_at_station
                self.docking_at_station = None
                return


        elif self.engine_lit and self.docked_at_station is None:
            force = self.engine_newtons * (self.engine_boost_multiple if self.engine_boosted else 1)
            adj_meters_per_second = float(force / self.mass)
            adj_meters_per_frame = float(adj_meters_per_second / fps)

            delta_x, delta_y = utils2d.calculate_x_y_components(
                adj_meters_per_frame,
                self.heading,
            )
            self.velocity_x_meters_per_second += delta_x
            self.velocity_y_meters_per_second += delta_y

        if self.is_stationary:
            # No velocity: coordinates are unchanges
            return

        # Calculate new coordinates with current velocity.
        distance_meters, heading = utils2d.calculate_resultant_vector(
            self.velocity_x_meters_per_second,
            self.velocity_y_meters_per_second,
        )
        distance_map_units = round((distance_meters * self.map_units_per_meter) / fps)

        self.coord_x, self.coord_y = utils2d.translate_point(
            (self.coord_x, self.coord_y),
            heading,
            distance_map_units,
        )

    def use_ebeam_charge(self, fps: int) -> bool:
        if not self.ebeam_firing:
            return False
        delta_ebeam_charge = self.ebeam_discharge_rate_per_second / fps
        if delta_ebeam_charge > self.ebeam_charge:
            self.ebeam_firing = False
            self.ebeam_charge = 0
            return False
        self.ebeam_charge = round(self.ebeam_charge - delta_ebeam_charge)
        return True

    def advance_damage_properties(self, game_frame: int, map_x: int, map_y: int, fps: int) -> Optional[Tuple]:
        if self.died_on_frame is None:
            return

        elif self.exploded:
            return ShipDeathType.EXPLOSION, game_frame - self.died_on_frame

        elif self.explode_immediately:
            self.explode()
            return ShipDeathType.EXPLOSION_NEW, game_frame - self.died_on_frame

        elif self.aflame_since_frame is None:
            # Ship not aflame yet and has not yet exploded
            seconds_since =  (game_frame - self.died_on_frame) / fps
            if seconds_since > self._seconds_to_aflame:
                self.aflame_since_frame = game_frame
                return ShipDeathType.AFLAME, game_frame - self.died_on_frame

        elif self.aflame_since_frame:
            # ship is onfire and it's going to explode
            seconds_aflame = (game_frame - self.aflame_since_frame) / fps
            if seconds_aflame > self._seconds_to_explode:
                self.explode()
                return ShipDeathType.EXPLOSION_NEW, game_frame - self.died_on_frame
            return ShipDeathType.AFLAME, game_frame - self.died_on_frame

    def explode(self):
        self.exploded = True
        self.aflame_since_frame = None
        self.velocity_x_meters_per_second = 0
        self.velocity_y_meters_per_second = 0

    def die(self, game_frame: int):
        self.died_on_frame = game_frame
        self.engine_lit = False
        self.engine_starting = False
        self.engine_online = False
        self.scanner_online = False
        self.scanner_starting = False
        self.ebeam_firing = False
        self.ebeam_charging = False
        self.autopilot_program = None
        self.gravity_brake_active = False
        self.gravity_brake_position = 0
        self.gravity_brake_extending = False
        self.gravity_brake_retracting = False
        self.mining_ore = False
        self.parked_at_ore_mine = None

    def emp(self, electricity_drain: int):
        self.engine_lit = False
        self.engine_starting = False
        self.engine_online = False
        self.engine_startup_power_used = 0
        self.scanner_online = False
        self.scanner_starting = False
        self.scanner_startup_power_used = 0
        self.ebeam_firing = False
        self.ebeam_charging = False
        self.ebeam_charge = 0
        self.autopilot_program = None
        self.gravity_brake_active = False
        self.gravity_brake_position = 0
        self.gravity_brake_extending = False
        self.gravity_brake_retracting = False
        self.docking_at_station = None
        self.docked_at_station = None
        self.mining_ore = False
        self.apu_online = False
        self.apu_starting = False
        self.apu_startup_power_used = 0

        self.battery_power = max(
            0,
            self.battery_power - electricity_drain
        )

    def advance_thermal_signature(self, fps: int) -> None:
        delta = -1 * self.scanner_thermal_signature_dissipation_per_second / fps
        if self.engine_lit:
            multiple = self.engine_boost_multiple if self.engine_boosted else 1
            delta += ((multiple * self.engine_lit_thermal_signature_rate_per_second) / fps)
        if self.ebeam_charging:
            delta += self.ebeam_charge_thermal_signature_rate_per_second / fps
        if self.apu_online:
            delta += self.apu_online_thermal_signature_rate_per_second / fps
        self.scanner_thermal_signature = max(
            0,
            round(self.scanner_thermal_signature + delta)
        )

    def run_autopilot(self) -> None:
        if not self.autopilot_program:
            return

        if self.autopilot_program == AutoPilotPrograms.HEADING_LOCK_ON_TARGET:
            if not self.scanner_locked or not self.scanner_lock_target:
                self.autopilot_program = None
                return
            self._set_heading(self.scanner_ship_data[self.scanner_lock_target]["relative_heading"])

        elif self.autopilot_program == AutoPilotPrograms.HEADING_LOCK_PROGRADE:
            _, angle = utils2d.calculate_resultant_vector(
                self.velocity_x_meters_per_second,
                self.velocity_y_meters_per_second)
            self._set_heading(angle)

        elif self.autopilot_program == AutoPilotPrograms.HEADING_LOCK_RETROGRADE:
            _, angle = utils2d.calculate_resultant_vector(
                self.velocity_x_meters_per_second,
                self.velocity_y_meters_per_second)
            self._set_heading(utils2d.invert_heading(angle))

        elif self.autopilot_program == AutoPilotPrograms.POSITION_HOLD:
            self._autopilot_hold_position()

        elif self.autopilot_program == AutoPilotPrograms.HEADING_LOCK_WAYPOINT:
            self._autopilot_heading_to_waypoint()

    def _autopilot_heading_to_waypoint(self):
        wp_uuid = self.autopilot_waypoint_uuid
        wp_type = self.autopilot_waypoint_type
        if(wp_uuid is None or wp_type is None):
            return
        if wp_type == MapFeatureType.ORE:
            feature = self._ore_mines[wp_uuid]
        elif wp_type == MapFeatureType.SPACE_STATION:
            feature = self._space_stations[wp_uuid]
        else:
            raise AutopilotError(f"unknown waypoint type {wp_type}")

        new_heading = utils2d.calculate_heading_to_point(
            self.coords,
            (
                feature['position_map_units_x'],
                feature['position_map_units_y'],
            ),
        )
        if new_heading != self.heading:
            self._set_heading(new_heading)


    def _autopilot_hold_position(self):
        if round(abs(self.velocity_x_meters_per_second)) <= 3 and round(abs(self.velocity_y_meters_per_second)) <= 3:
            # Force the ship to stop moving and end Autopilot program
            # If ship velocity is slow enough.
            self.velocity_x_meters_per_second = 0
            self.velocity_y_meters_per_second = 0
            self.engine_lit = False
            self.autopilot_program = None
            return

        if not self.engine_online:
            self.autopilot_program = None
            return

        _, angle = utils2d.calculate_resultant_vector(
            self.velocity_x_meters_per_second,
            self.velocity_y_meters_per_second)
        new_heading = utils2d.invert_heading(angle)
        if new_heading != self.heading:
            self._set_heading(new_heading)

        if not self.engine_lit:
            self.engine_lit = True

    def advance_gravity_brake_position(self, fps: int) -> None:
        if not self.gravity_brake_retracting and not self.gravity_brake_extending:
            return

        if self.gravity_brake_extending:
            if self.gravity_brake_deployed:
                self.gravity_brake_extending = False
                return
            delta = min(
                max(1, round(self.gravity_brake_traversal_per_second / fps)),
                self.gravity_brake_deployed_position - self.gravity_brake_position,
            )
            self.gravity_brake_position += delta
            return

        elif self.gravity_brake_retracting:
            if self.gravity_brake_position == 0:
                self.gravity_brake_retracting = False
                return
            delta = min(
                max(1, round(self.gravity_brake_traversal_per_second / fps)),
                self.gravity_brake_position
            )
            self.gravity_brake_position -= delta
            return

        else:
            raise NotImplementedError

    def advance_upgrades(self, fps: int) -> None:
        # CORE UPGRADES # #
        core_ix_to_remove = []
        utype = UpgradeType.CORE
        for ix in self._core_upgrade_active_indexes:
            new_seconds = self._upgrades[utype][ix].seconds_researched + (1 / fps)
            if new_seconds >= self._upgrades[utype][ix].cost['seconds']:
                # core upgrade complete
                # Update SSOT
                self._upgrades[utype][ix].earned = True
                self._upgrades[utype][ix].seconds_researched = None
                # Update Front end summary
                self._upgrade_summary[utype][
                        self._upgrades[utype][ix].slug
                    ]['seconds_researched'] = None
                self._upgrade_summary[utype][
                        self._upgrades[utype][ix].slug
                    ]['current_level'] = 1
                self._upgrade_summary[utype][
                        self._upgrades[utype][ix].slug
                    ]['current_cost']  = None
                core_ix_to_remove.append(ix)
            else:
                # Update SSOT
                self._upgrades[utype][ix].seconds_researched = new_seconds
                # Update Front end summary
                self._upgrade_summary[utype][
                    self._upgrades[utype][ix].slug
                ]['seconds_researched'] = new_seconds
        if core_ix_to_remove:
            self._core_upgrade_active_indexes = [
                v for v in self._core_upgrade_active_indexes
                if v not in core_ix_to_remove
            ]

        # SHIP UPGRADES # #
        ship_ix_to_remove = []
        utype = UpgradeType.SHIP
        for ix in self._ship_upgrade_active_indexes:
            level_researching = self._upgrades[utype][ix].current_level + 1
            cost = self._upgrades[utype][ix].cost_progression[level_researching]
            new_seconds = self._upgrades[utype][ix].seconds_researched + (1 / fps)
            if new_seconds >= cost['seconds']:
                # ship upgrade complete
                # Update SSOT
                self._upgrades[utype][ix].seconds_researched = None
                new_level = self._upgrades[utype][ix].current_level + 1
                self._upgrades[utype][ix].current_level = new_level
                # Update Front end summary
                self._upgrade_summary[utype][
                        self._upgrades[utype][ix].slug
                    ]['seconds_researched'] = None
                self._upgrade_summary[utype][
                        self._upgrades[utype][ix].slug
                    ]['current_level']  = new_level
                next_level = new_level + 1 if self._upgrades[utype][ix].max_level > new_level else None
                self._upgrade_summary[utype][
                        self._upgrades[utype][ix].slug
                    ]['current_cost'] = None if next_level is None else self._upgrades[utype][ix].cost_progression[
                        next_level
                    ]
                # Apply effects to ship.
                for effect in self._upgrades[utype][ix].effect_progression[new_level]:
                    current_stat = getattr(self, effect['field'])
                    setattr(self, effect['field'], current_stat + effect['delta'])
                ship_ix_to_remove.append(ix)
            else:
                # Update SSOT
                self._upgrades[utype][ix].seconds_researched = new_seconds
                # Update Front end summary
                self._upgrade_summary[utype][
                    self._upgrades[utype][ix].slug
                ]['seconds_researched'] = new_seconds
        if ship_ix_to_remove:
            self._ship_upgrade_active_indexes = [
                v for v in self._ship_upgrade_active_indexes
                if v not in ship_ix_to_remove
            ]

    def process_command(self, command: str, *args, **kwargs):
        if self.died_on_frame:
            return

        if command == ShipCommands.SET_HEADING:
            return self.cmd_set_heading(args[0])

        elif command == ShipCommands.ACTIVATE_ENGINE:
            self.cmd_activate_engine()
        elif command == ShipCommands.DEACTIVATE_ENGINE:
            self.cmd_deactivate_engine()
        elif command == ShipCommands.LIGHT_ENGINE:
            self.cmd_light_engine()
        elif command == ShipCommands.BOOST_ENGINE:
            self.cmd_boost_engine()
        elif command == ShipCommands.UNLIGHT_ENGINE:
            self.cmd_unlight_engine()

        elif command == ShipCommands.ACTIVATE_APU:
            self.cmd_activate_apu()
        elif command == ShipCommands.DEACTIVATE_APU:
            self.cmd_deactivate_apu()

        elif command == ShipCommands.ACTIVATE_SCANNER:
            self.cmd_activate_scanner()
        elif command == ShipCommands.DEACTIVATE_SCANNER:
            self.cmd_deactivate_scanner()
        elif command == ShipCommands.SET_SCANNER_MODE_RADAR:
            self.cmd_set_scanner_mode_radar()
        elif command == ShipCommands.SET_SCANNER_MODE_IR:
            self.cmd_set_scanner_mode_ir()
        elif command == ShipCommands.SET_SCANNER_LOCK_TARGET:
            self.cmd_set_scanner_lock_target(args[0])

        elif command == ShipCommands.CHARGE_EBEAM:
            self.cmd_charge_ebeam()
        elif command == ShipCommands.PAUSE_CHARGE_EBEAM:
            self.cmd_pause_charge_ebeam()
        elif command == ShipCommands.FIRE_EBEAM:
            self.cmd_fire_ebeam()

        elif command == ShipCommands.RUN_AUTOPILOT_PROGRAM:
            self.cmd_run_autopilot_program(args[0])
        elif command == ShipCommands.RUN_AUTOPILOT_HEADING_TO_WAYPOINT:
            self.cmd_run_autopilot_program_heading_to_waypoint(
                kwargs['waypointUUID'], kwargs['waypointType']
            )
        elif command == ShipCommands.DISABLE_AUTO_PILOT:
            self.cmd_disable_autopilot()

        elif command == ShipCommands.EXTEND_GRAVITY_BRAKE:
            self.cmd_extend_gravity_brake()
        elif command == ShipCommands.RETRACT_GRAVITY_BRAKE:
            self.cmd_retract_gravity_brake()

        elif command == ShipCommands.START_ORE_MINING:
            self.cmd_start_ore_mining()
        elif command == ShipCommands.STOP_ORE_MINING:
            self.cmd_stop_ore_mining()
        elif command == ShipCommands.TRADE_ORE_FOR_ORE_COIN:
            self.cmd_trade_ore_for_ore_coin(kwargs['game_frame'])

        elif command == ShipCommands.START_FUELING:
            self.cmd_start_fueling()
        elif command == ShipCommands.STOP_FUELING:
            self.cmd_stop_fueling()

        elif command == ShipCommands.START_CORE_UPGRADE:
            self.cmd_start_core_upgrade(args[0])
        elif command == ShipCommands.START_SHIP_UPGRADE:
            self.cmd_start_ship_upgrade(args[0])
        elif command == ShipCommands.CANCEL_CORE_UPGRADE:
            self.cmd_cancel_core_upgrade(args[0])
        elif command == ShipCommands.CANCEL_SHIP_UPGRADE:
            self.cmd_cancel_ship_upgrade(args[0])

        elif command == ShipCommands.BUY_MAGNET_MINE:
            self.cmd_buy_magnet_mine()
        elif command == ShipCommands.LAUNCH_MAGNET_MINE:
            self.cmd_launch_magnet_mine(args[0])
        elif command == ShipCommands.BUY_EMP:
            self.cmd_buy_emp()
        elif command == ShipCommands.LAUNCH_EMP:
            self.cmd_launch_emp(args[0])
        elif command == ShipCommands.BUY_HUNTER_DRONE:
            self.cmd_buy_hunter_drone()
        elif command == ShipCommands.LAUNCH_HUNTER_DRONE:
            self.cmd_launch_hunter_drone(args[0])

        else:
            raise ShipCommandError("NotImplementedError")

    # Heading command
    def cmd_set_heading(self, heading: int):
        if self.autopilot_program:
            return
        if heading == self.heading:
            return
        if not (359 >= heading >= 0):
            raise ShipCommandError("invalid heading")

        self._set_heading(heading)

    def _set_heading(self, heading: int):
        self.heading = heading
        self._set_relative_coords()


    def _set_relative_coords(self) -> None:
        delta_radians = utils2d.degrees_to_radians(
            utils2d.heading_to_delta_heading_from_zero(self.heading)
        )

        self.rel_rot_coord_hitbox_nose = utils2d.rotate(
            constants.ORGIN_COORD,
            self.rel_fixed_coord_hitbox_nose,
            delta_radians,
        )
        self.rel_rot_coord_hitbox_bottom_left = utils2d.rotate(
            constants.ORGIN_COORD,
            self.rel_fixed_coord_hitbox_bottom_left,
            delta_radians,
        )
        self.rel_rot_coord_hitbox_bottom_center = utils2d.rotate(
            constants.ORGIN_COORD,
            self.rel_fixed_coord_hitbox_bottom_center,
            delta_radians,
        )
        self.rel_rot_coord_hitbox_bottom_right = utils2d.rotate(
            constants.ORGIN_COORD,
            self.rel_fixed_coord_hitbox_bottom_right,
            delta_radians,
        )

    # Engine Commands
    def cmd_activate_engine(self) -> None:
        if self.engine_online:
            return
        if self.engine_starting:
            return
        self.engine_starting = True
        self.engine_startup_power_used = 0

    def cmd_deactivate_engine(self) -> None:
        if not self.engine_online:
            return
        self.engine_lit = False
        self.engine_online = False

    def cmd_unlight_engine(self) -> None:
        if not self.engine_lit:
            return
        self.engine_lit = False

    def cmd_light_engine(self) -> None:
        if not self.engine_online or self.engine_lit:
            return
        self.engine_lit = True

    def cmd_boost_engine(self) -> None:
        if not self.engine_online or not self.engine_lit:
            return
        self.engine_boosting = True

    # Scanner Commands
    def cmd_activate_scanner(self) -> None:
        if self.scanner_online or self.scanner_starting:
            return
        self.scanner_startup_power_used = 0
        self.scanner_starting = True

    def cmd_deactivate_scanner(self) -> None:
        if not self.scanner_online or self.scanner_starting:
            return
        self.scanner_online = False
        self.scanner_locked = False
        self.scanner_locking = False
        self.scanner_locking_power_used = None
        self.scanner_lock_target = None
        self.scanner_lock_traversal_degrees_previous_frame = None
        self.scanner_lock_traversal_slack = None
        self.scanner_ship_data.clear()

    def cmd_set_scanner_mode_radar(self) -> None:
        self.scanner_mode = ShipScannerMode.RADAR

    def cmd_set_scanner_mode_ir(self) -> None:
        self.scanner_mode = ShipScannerMode.IR

    def cmd_set_scanner_lock_target(self, target_id: str) -> None:
        if not self.scanner_online or self.scanner_locking:
            return
        if target_id not in self.scanner_ship_data:
            return
        self.scanner_locking = True
        self.scanner_locked = False
        self.scanner_locking_power_used = 0
        self.scanner_lock_target = target_id
        self.scanner_lock_traversal_degrees_previous_frame = None

    def cmd_charge_ebeam(self):
        if not self.ebeam_charging:
            self.ebeam_charging = True

    def cmd_pause_charge_ebeam(self):
        if self.ebeam_charging:
            self.ebeam_charging = False

    def cmd_fire_ebeam(self):
        if self.ebeam_charging:
            self.ebeam_charging = False
        if self.ebeam_firing:
            return
        if self.ebeam_charge >= self.ebeam_charge_fire_minimum:
            self.ebeam_firing = True

    def cmd_run_autopilot_program(self, program_name: str):
        if program_name == AutoPilotPrograms.POSITION_HOLD:
            if self.engine_online:
                self.autopilot_program = program_name
        elif (
            program_name == AutoPilotPrograms.HEADING_LOCK_PROGRADE
            or program_name == AutoPilotPrograms.HEADING_LOCK_RETROGRADE
        ):
            self.autopilot_program = program_name
        elif program_name == AutoPilotPrograms.HEADING_LOCK_ON_TARGET:
            if self.scanner_locked:
                self.autopilot_program = program_name

    def cmd_run_autopilot_program_heading_to_waypoint(
        self,
        waypoint_uuid: str,
        waypoint_type: str,
    ):
        self.autopilot_program = AutoPilotPrograms.HEADING_LOCK_WAYPOINT
        self.autopilot_waypoint_uuid = waypoint_uuid
        self.autopilot_waypoint_type = waypoint_type

    def cmd_disable_autopilot(self):
        if self.autopilot_program:
            if self.autopilot_program == AutoPilotPrograms.POSITION_HOLD:
                self.engine_lit = False
            self.autopilot_program = None
            self.autopilot_waypoint_uuid = None
            self.autopilot_waypoint_type = None

    def cmd_activate_apu(self):
        if not self.apu_online and not self.apu_starting:
            self.apu_starting = True
            self.apu_startup_power_used = 0

    def cmd_deactivate_apu(self):
        if self.apu_online:
            self.apu_online = False

    def cmd_extend_gravity_brake(self):
        if self.gravity_brake_extending or self.gravity_brake_retracting:
            return
        self.gravity_brake_extending = True

    def cmd_retract_gravity_brake(self):
        if self.gravity_brake_extending or self.gravity_brake_retracting:
            return
        self.gravity_brake_retracting = True
        self.docked_at_station = None
        self.docking_at_station = None

    def cmd_start_ore_mining(self):
        if not self.parked_at_ore_mine:
            return
        self.mining_ore = True

    def cmd_stop_ore_mining(self):
        self.mining_ore = False

    def cmd_trade_ore_for_ore_coin(self, game_frame: int):
        if not self.docked_at_station:
            return
        if not self.cargo_ore_mass_kg > 0:
            return
        deposit_amount = self.cargo_ore_mass_kg
        self.cargo_ore_mass_kg = 0
        self.virtual_ore_kg += deposit_amount
        self.last_ore_deposit_frame = game_frame

    def cmd_start_fueling(self):
        if not self.docked_at_station or not self.gravity_brake_deployed:
            return
        if self.fueling_at_station:
            return
        self.fueling_at_station = True

    def cmd_stop_fueling(self):
        if not self.fueling_at_station:
            return
        self.fueling_at_station = False

    def _can_afford_upgrade(self, cost: UpgradeCost):
        avail_ore = self.virtual_ore_kg + self.cargo_ore_mass_kg
        if avail_ore < cost['ore']:
            return False
        if self.battery_power < cost['electricity']:
            return False
        return True

    def cmd_start_core_upgrade(self, slug: str) -> None:
        utype = UpgradeType.CORE
        if not self.docked_at_station:
            return
        upgrade = None
        upgrade_ix = None
        for ix, u in enumerate(self._upgrades[utype]):
            if u.slug == slug:
                upgrade = u
                upgrade_ix = ix
                break
        if upgrade is None:
            return
        if upgrade.earned:
            return
        if upgrade.seconds_researched is not None:
            # Already researching.
            return
        if not self._can_afford_upgrade(upgrade.cost):
            return

        self.use_battery_power(upgrade.cost['electricity'])
        self.withdraw_ore(upgrade.cost['ore'])
        self._upgrades[utype][upgrade_ix].seconds_researched = 0
        self._core_upgrade_active_indexes.append(upgrade_ix)
        self._upgrade_summary[utype][slug]['seconds_researched'] = 0

    def cmd_start_ship_upgrade(self, slug: str) -> None:
        utype = UpgradeType.SHIP
        upgrade = None
        upgrade_ix = None
        for ix, u in enumerate(self._upgrades[utype]):
            if u.slug == slug:
                upgrade = u
                upgrade_ix = ix
                break
        if upgrade is None:
            return # "not found"
        if upgrade.seconds_researched is not None:
            # Already researching.
            return # "already researching"
        if upgrade.at_max_level():
            return # "at max level"
        next_level = upgrade.current_level + 1
        required_core_upgrades = upgrade.required_core_upgrades.get(next_level, [])
        earned_core_upgrades = set(
            u.slug
            for u in self._upgrades[UpgradeType.CORE]
            if u.earned
        )
        missing = any(u for u in required_core_upgrades if u not in earned_core_upgrades)
        if missing:
            # Missing core upgrade(s)
            return # "missing upgrade"
        cost = upgrade.cost_progression[next_level]
        if not self._can_afford_upgrade(cost):
            return # "not enough resources"
        self.use_battery_power(cost['electricity'])
        self.withdraw_ore(cost['ore'])
        self._upgrades[utype][upgrade_ix].seconds_researched = 0
        self._ship_upgrade_active_indexes.append(upgrade_ix)
        self._upgrade_summary[utype][slug]['seconds_researched'] = 0

    def cmd_cancel_core_upgrade(self, slug: str) -> None:
        self._cancel_upgrade(UpgradeType.CORE, slug)

    def cmd_cancel_ship_upgrade(self, slug: str) -> None:
        self._cancel_upgrade(UpgradeType.SHIP, slug)

    def _cancel_upgrade(self, utype: str, slug: str):
        if utype != UpgradeType.SHIP and utype != UpgradeType.CORE:
            raise Exception("invalid utype")

        upgrade = None
        upgrade_ix = None
        for ix, u in enumerate(self._upgrades[utype]):
            if u.slug == slug:
                upgrade = u
                upgrade_ix = ix
                break
        if upgrade is None:
            return # "not found"
        if upgrade.seconds_researched is None:
            return # "not researching"

        # refund resources
        if utype == UpgradeType.CORE:
            cost = upgrade.cost
        elif utype == UpgradeType.SHIP:
            cost = upgrade.cost_progression[upgrade.current_level + 1]
        else:
            raise NotImplementedError

        self.virtual_ore_kg += (cost['ore'] * 0.75)
        self.charge_battery(cost['electricity'])

        self._upgrades[utype][upgrade_ix].seconds_researched = None
        if utype == UpgradeType.CORE:
            self._core_upgrade_active_indexes = [
                    v for v in self._core_upgrade_active_indexes
                    if v != upgrade_ix
                ]
        elif utype == UpgradeType.SHIP:
            self._ship_upgrade_active_indexes = [
                    v for v in self._ship_upgrade_active_indexes
                    if v != upgrade_ix
                ]
        else:
            raise NotImplementedError

        self._upgrade_summary[utype][
                self._upgrades[utype][upgrade_ix].slug
            ]['seconds_researched'] = None

    # TUBE WEAPON COMMANDS
    def cmd_buy_magnet_mine(self):
        if self.special_weapons_loaded >= self.special_weapons_tubes_count:
            return
        if not self.docked_at_station:
            return
        ore_cost = self._special_weapon_costs[constants.MAGNET_MINE_SLUG]
        try:
            self.withdraw_ore(ore_cost)
        except InsufficientOreError:
            return
        self.magnet_mines_loaded += 1

    def cmd_launch_magnet_mine(self, launch_velocity: int):
        _velocity = max(
            launch_velocity,
            self._special_weapons_min_launch_velocity,
        )
        _velocity = min(
            _velocity,
            self._special_weapons_max_launch_velocity,
        )
        if self.magnet_mines_loaded > 0 and not self.magnet_mine_firing:
            self.magnet_mines_loaded -= 1
            self.magnet_mine_firing = True
            self._special_weapons_launch_velocity = _velocity

    def cmd_buy_emp(self):
        if self.special_weapons_loaded >= self.special_weapons_tubes_count:
            return
        if not self.docked_at_station:
            return
        ore_cost = self._special_weapon_costs[constants.EMP_SLUG]
        try:
            self.withdraw_ore(ore_cost)
        except InsufficientOreError:
            return
        self.emps_loaded += 1

    def cmd_launch_emp(self, launch_velocity: int):
        _velocity = max(
            launch_velocity,
            self._special_weapons_min_launch_velocity,
        )
        _velocity = min(
            _velocity,
            self._special_weapons_max_launch_velocity,
        )
        if self.emps_loaded > 0 and not self.emp_firing:
            self.emps_loaded -= 1
            self.emp_firing = True
            self._special_weapons_launch_velocity = _velocity

    def cmd_buy_hunter_drone(self):
        if self.special_weapons_loaded >= self.special_weapons_tubes_count:
            return
        if not self.docked_at_station:
            return
        ore_cost = self._special_weapon_costs[constants.HUNTER_DRONE_SLUG]
        try:
            self.withdraw_ore(ore_cost)
        except InsufficientOreError:
            return
        self.hunter_drones_loaded += 1

    def cmd_launch_hunter_drone(self, launch_velocity: int):
        _velocity = max(
            launch_velocity,
            self._special_weapons_min_launch_velocity,
        )
        _velocity = min(
            _velocity,
            self._special_weapons_max_launch_velocity,
        )
        if self.hunter_drones_loaded > 0 and not self.hunter_drone_firing:
            self.hunter_drones_loaded -= 1
            self.hunter_drone_firing = True
            self._special_weapons_launch_velocity = _velocity
