
import random
import datetime as dt
from typing import Tuple, Dict, TypedDict, Optional, Generator, List, Union

from api.models.base import BaseModel
from api import utils2d
from api import constants


class ShipCommandError(Exception):
    pass

class InsufficientPowerError(ShipCommandError):
    pass

class InsufficientFuelError(ShipCommandError):
    pass

class ShipCoatType:
    NONE = None
    RADAR_DEFEATING = "radar_defeating"

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
    DISABLE_AUTO_PILOT = 'disable_autopilot'

    CHARGE_EBEAM = 'charge_ebeam'
    PAUSE_CHARGE_EBEAM = 'pause_charge_ebeam'
    FIRE_EBEAM = 'fire_ebeam'

    EXTEND_GRAVITY_BRAKE = "extend_gravity_brake"
    RETRACT_GRAVITY_BRAKE = "retract_gravity_brake"

class ShipStateKey:
    MASS = 'mass'

class ShipDeathType:
    EXPLOSION = 'explosion'
    AFLAME = 'aflame'
    ADRIFT = 'adrift'

class ShipScannerMode:
    RADAR = 'radar'
    IR = 'ir'


class VisibleElementShapeType:
    ARC = 'arc'
    RECT = 'rect'

class ScannedElementType:
    SHIP = 'ship'
    FIXTURE = 'fixture'
    SCRAP = 'scrap'

class ScannedElement(TypedDict):
    id: str
    designator: str
    element_type: str
    thermal_signature: Optional[int]
    coord_x: int
    coord_y: int
    relative_heading: Optional[int] # Rounded int describing bearing to element
    target_heading: Optional[float] # Float describing beaing to element
    distance: Optional[int]

    visual_p0: Tuple[int]
    visual_p1: Tuple[int]
    visual_p2: Tuple[int]
    visual_p3: Tuple[int]

    visual_fill_color: Optional[str]
    visual_stroke_color: Optional[str]
    visual_shape: Optional[str]     # 'arc' or 'rect'
    visual_radius: Optional[int]    # arc
    visual_polygon_points: Optional[List[Tuple]]
    visual_engine_lit: Optional[bool] #
    visual_ebeam_charging: Optional[bool] #
    visual_ebeam_firing: Optional[bool] #


class TimerItem(TypedDict):
    name: str
    percent: int


class AutoPilotPrograms:
    POSITION_HOLD = 'position_hold'
    HEADING_LOCK_ON_TARGET = 'lock_target'
    HEADING_LOCK_PROGRADE = 'lock_prograde'
    HEADING_LOCK_RETROGRADE = 'lock_retrograde'


class Ship(BaseModel):
    def __init__(self):
        super().__init__()

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

        # relative rotated coordinate boundaries of the ship, rotated to account for the ship's heading.
        # These coords will change when the ship's heading changes.
        self.rel_rot_coord_0 = (None, None,)
        self.rel_rot_coord_1 = (None, None,)
        self.rel_rot_coord_2 = (None, None,)
        self.rel_rot_coord_3 = (None, None,)
        self.fin_0_rel_rot_coord_0 = (None, None,)
        self.fin_0_rel_rot_coord_1 = (None, None,)
        self.fin_1_rel_rot_coord_0 = (None, None,)
        self.fin_1_rel_rot_coord_1 = (None, None,)


        # relative coordinate boundaries of the ship with heading fixed to zero.
        # These coords will NOT change unless the ship size changes
        self.heading_0_rel_coord_0 = (None, None,)
        self.heading_0_rel_coord_1 = (None, None,)
        self.heading_0_rel_coord_2 = (None, None,)
        self.heading_0_rel_coord_3 = (None, None,)
        self.heading_0_fin_0_rel_coord_0 = (None, None,)
        self.heading_0_fin_0_rel_coord_1 = (None, None,)
        self.heading_0_fin_1_rel_coord_0 = (None, None,)
        self.heading_0_fin_1_rel_coord_1 = (None, None,)

        # </END OF RELATIVE COORDINATES>

        # Velocity
        self.velocity_x_meters_per_second = float(0)
        self.velocity_y_meters_per_second = float(0)

        self.visual_range = None

        # Battery
        self.battery_power = 0
        self.battery_capacity = 0
        self.battery_mass = 0

        # Fuel Tank
        self.fuel_level = 0
        self.fuel_capacity = 0

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
        self.scanner_data: Dict[str, ScannedElement] = {}
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
        self.ebeam_charge_thermal_signature_rate_per_second = None
        self.ebeam_charge = None
        self.ebeam_charge_capacity = None
        self.ebeam_charging = False
        self.ebeam_firing = False
        self.ebeam_charge_power_draw_multiple = None
        self.ebeam_discharge_rate_per_second = None
        self.ebeam_charge_fire_minimum = None
        self.ebeam_color = None

        self.autopilot_program = None

        # Damage
        self.died_on_frame = None
        self.aflame_since_frame = None
        self._seconds_to_aflame = random.randint(0, 1)
        self.explode_immediately = False # random.randint(0, 4) == 1
        self.explosion_frame = None
        self.explosion_point = None
        self._seconds_to_explode = 10 # random.randint(2, 4)

        # Space station interactions
        self.docked_at_station = None
        self.docking_at_station = None
        self.gravity_brake_position = 0
        self.gravity_brake_deployed_position = 100
        self.gravity_brake_traversal_per_second = None
        self.gravity_brake_retracting = False
        self.gravity_brake_extending = False
        self.gravity_brake_active = False # flipped to true, the ship rapidly slows down.

        # Arbitrary ship state data
        self._state = {}

    @property
    def coords(self) -> Tuple[int]:
        return (self.coord_x, self.coord_y,)

    @property
    def h0_x1(self) -> int:
        return self.heading_0_rel_coord_0[0]

    @property
    def h0_y1(self) -> int:
        return self.heading_0_rel_coord_0[1]

    @property
    def h0_x2(self) -> int:
        return self.heading_0_rel_coord_2[0]

    @property
    def h0_y2(self) -> int:
        return self.heading_0_rel_coord_2[1]

    @property
    def map_p0(self) -> Tuple:
        return (
            self.coord_x + self.rel_rot_coord_0[0],
            self.coord_y + self.rel_rot_coord_0[1],
        )

    @property
    def map_p1(self) -> Tuple:
        return (
            self.coord_x + self.rel_rot_coord_1[0],
            self.coord_y + self.rel_rot_coord_1[1],
        )

    @property
    def map_p2(self) -> Tuple:
        return (
            self.coord_x + self.rel_rot_coord_2[0],
            self.coord_y + self.rel_rot_coord_2[1],
        )

    @property
    def map_p3(self) -> Tuple:
        return (
            self.coord_x + self.rel_rot_coord_3[0],
            self.coord_y + self.rel_rot_coord_3[1],
        )

    @property
    def ebeam_heading(self) -> Union[float, int]:
        if self.scanner_lock_target and self.scanner_locked and self.autopilot_program == AutoPilotPrograms.HEADING_LOCK_ON_TARGET:
            return self.scanner_data[self.scanner_lock_target]['target_heading']
        return self.heading


    @property
    def hitbox_lines(self) -> Tuple[Tuple[Tuple]]:
        return (
            (self.map_p0, self.map_p1,),
            (self.map_p1, self.map_p2,),
            (self.map_p2, self.map_p3,),
            (self.map_p3, self.map_p0,),
        )

    @property
    def map_fin_0_coord_0(self) -> Tuple:
        return (
            self.coord_x + self.fin_0_rel_rot_coord_0[0],
            self.coord_y + self.fin_0_rel_rot_coord_0[1],
        )

    @property
    def map_fin_0_coord_1(self) -> Tuple:
        return (
            self.coord_x + self.fin_0_rel_rot_coord_1[0],
            self.coord_y + self.fin_0_rel_rot_coord_1[1],
        )

    @property
    def map_fin_1_coord_0(self) -> Tuple:
        return (
            self.coord_x + self.fin_1_rel_rot_coord_0[0],
            self.coord_y + self.fin_1_rel_rot_coord_0[1],
        )

    @property
    def map_fin_1_coord_1(self) -> Tuple:
        return (
            self.coord_x + self.fin_1_rel_rot_coord_1[0],
            self.coord_y + self.fin_1_rel_rot_coord_1[1],
        )

    @property
    def mass(self) -> int:
        return self._state.get(ShipStateKey.MASS, (
            self.battery_mass
            + self.engine_mass
            + int(self.fuel_level / constants.FUEL_MASS_UNITS_PER_KG)
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
    def gravity_brake_deployed(self) -> bool:
        return self.gravity_brake_position == self.gravity_brake_deployed_position


    def to_dict(self) -> Dict:
        """ Get JSON serializable representation of the ship.
        """
        return {
            'id': self.id,
            'team_id': self.team_id,
            'mass': self.mass,
            'coord_x': self.coord_x,
            'coord_y': self.coord_y,
            'heading': self.heading,
            'rel_rot_coord_0': self.rel_rot_coord_0,
            'rel_rot_coord_1': self.rel_rot_coord_1,
            'rel_rot_coord_2': self.rel_rot_coord_2,
            'rel_rot_coord_3': self.rel_rot_coord_3,
            "fin_0_rel_rot_coord_0":  self.fin_0_rel_rot_coord_0,
            "fin_0_rel_rot_coord_1":  self.fin_0_rel_rot_coord_1,
            "fin_1_rel_rot_coord_0":  self.fin_1_rel_rot_coord_0,
            "fin_1_rel_rot_coord_1":  self.fin_1_rel_rot_coord_1,
            'velocity_x_meters_per_second': self.velocity_x_meters_per_second,
            'velocity_y_meters_per_second': self.velocity_y_meters_per_second,
            'battery_power': self.battery_power,
            'battery_capacity': self.battery_capacity,
            'fuel_level': self.fuel_level,
            'fuel_capacity': self.fuel_capacity,

            'engine_newtons': self.engine_newtons,
            'engine_online': self.engine_online,
            'engine_lit': self.engine_lit,
            'engine_starting': self.engine_starting,
            'engine_boosted': self.engine_boosted,
            'engine_boosted_last_frame': self.engine_boosted_last_frame,

            'apu_starting': self.apu_starting,
            'apu_online': self.apu_online,

            'scanner_online': self.scanner_online,
            'scanner_locking': self.scanner_locking,
            'scanner_locked': self.scanner_locked,
            'scanner_lock_target': self.scanner_lock_target,
            'scanner_starting': self.scanner_starting,
            'scanner_mode': self.scanner_mode,
            'scanner_radar_range': self.scanner_radar_range,
            'scanner_ir_range': self.scanner_ir_range,
            'scanner_ir_minimum_thermal_signature': self.scanner_ir_minimum_thermal_signature,
            'scanner_data': list(self.scanner_data.values()),
            'scanner_thermal_signature': self.scanner_thermal_signature,
            'scanner_lock_traversal_slack': self.scanner_lock_traversal_slack,

            'ebeam_firing': self.ebeam_firing,
            'ebeam_charging': self.ebeam_charging,
            'ebeam_charge_capacity': self.ebeam_charge_capacity,
            'ebeam_color': self.ebeam_color,
            'ebeam_charge': self.ebeam_charge,
            'ebeam_can_fire': self.ebeam_charge >= self.ebeam_charge_fire_minimum and not self.ebeam_firing,

            'docked_at_station': self.docked_at_station,
            'gravity_brake_position': self.gravity_brake_position,
            'gravity_brake_deployed_position': self.gravity_brake_deployed_position,
            'gravity_brake_retracting': self.gravity_brake_retracting,
            'gravity_brake_extending': self.gravity_brake_extending,
            'gravity_brake_active': self.gravity_brake_active,
            'gravity_brake_deployed': self.gravity_brake_deployed,

            'alive': self.died_on_frame is None,
            'aflame': self.aflame_since_frame is not None,
            'explosion_frame': self.explosion_frame,

            'visual_range': self.visual_range,

            'autopilot_program': self.autopilot_program,

            'timers': list(self.get_timer_items()),
        }

    @classmethod
    def spawn(cls, team_id: str, map_units_per_meter: int = 1) -> "Ship":
        """ Create new unpositioned ship with defaults
        """
        instance = cls()

        instance.map_units_per_meter = map_units_per_meter
        instance.team_id = team_id

        x_len = constants.SHIP_X_LEN * map_units_per_meter
        y_len = constants.SHIP_Y_LEN * map_units_per_meter

        x1 = round((x_len / 2) * -1)
        x2 = round(x_len / 2)
        y1 = round((y_len / 2) * -1)
        y2 = round(y_len / 2)

        instance.heading_0_rel_coord_0 = (x1, y1,)
        instance.heading_0_rel_coord_1 = (x1, y2,)
        instance.heading_0_rel_coord_2 = (x2, y2,)
        instance.heading_0_rel_coord_3 = (x2, y1,)

        instance.rel_rot_coord_0 = (x1, y1,)
        instance.rel_rot_coord_1 = (x1, y2,)
        instance.rel_rot_coord_2 = (x2, y2,)
        instance.rel_rot_coord_3 = (x2, y1,)

        # Tail Fin coords
        fin_top_y = y1 + round(y_len / 4)
        fin_bot_y  = y1
        fin_0_bot_x = round(x1 - (x_len / 1.45))
        fin_1_bot_x = round(x2 + (x_len / 1.45))

        instance.heading_0_fin_0_rel_coord_0 = (x1, fin_top_y,)
        instance.heading_0_fin_0_rel_coord_1 = (fin_0_bot_x, fin_bot_y,)
        instance.heading_0_fin_1_rel_coord_0 = (x2, fin_top_y,)
        instance.heading_0_fin_1_rel_coord_1 = (fin_1_bot_x, fin_bot_y,)

        instance.fin_0_rel_rot_coord_0 = (x1, fin_top_y,)
        instance.fin_0_rel_rot_coord_1 = (fin_0_bot_x, fin_bot_y,)
        instance.fin_1_rel_rot_coord_0 = (x2, fin_top_y,)
        instance.fin_1_rel_rot_coord_1 = (fin_1_bot_x, fin_bot_y,)


        instance.battery_power = constants.BATTERY_STARTING_POWER
        instance.battery_capacity = constants.BATTERY_POWER_CAPACITY
        instance.battery_mass = constants.BATTERY_MASS

        instance.fuel_level = constants.FUEL_START_LEVEL
        instance.fuel_capacity = constants.FUEL_CAPACITY

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
        instance.ebeam_charge_thermal_signature_rate_per_second = constants.EBEAM_CHARGE_THERMAL_SIGNATURE_RATE_PER_SECOND
        instance.ebeam_charge = 0
        instance.ebeam_charge_capacity = constants.EBEAM_CHARGE_CAPACITY
        instance.ebeam_charge_power_draw_multiple = constants.EBEAM_CHARGE_BATTERY_POWER_DRAW_MULTIPLE
        instance.ebeam_discharge_rate_per_second = constants.EBEAM_DISCHARGE_RATE_PER_SECOND
        instance.ebeam_charge_fire_minimum = constants.EBEAM_CHARGE_FIRE_MINIMUM
        instance.ebeam_color = constants.EBEAM_COLOR_STARTING

        instance.gravity_brake_traversal_per_second = constants.GRAVITY_BRAKE_TRAVERSAL_PER_SECOND

        return instance


    def get_timer_items(self) -> Generator[TimerItem, None, None]:
        if self.engine_starting:
            yield {
                'name': 'Engine Startup',
                'percent': round(
                    self.engine_startup_power_used / self.engine_activation_power_required_total * 100
                ),
            }
        if self.scanner_starting:
            yield {
                'name': 'Scanner Startup',
                'percent': round(
                    self.scanner_startup_power_used / self.scanner_activation_power_required_total * 100
                ),
            }
        if self.scanner_locking:
            yield {
                'name': 'Scanner Locking',
                'percent': round(
                    self.scanner_locking_power_used / self.scanner_get_lock_power_requirement_total * 100
                ),
            }
        if self.ebeam_charge > 0:
            yield {
                'name': 'E-Beam Charge',
                'percent': round(
                    self.ebeam_charge / self.ebeam_charge_capacity * 100
                ),
            }
        if self.apu_starting:
            yield {
                'name': 'APU Startup',
                'percent': round(
                    self.apu_startup_power_used / self.apu_activation_power_required_total * 100
                ),
            }

        if self.gravity_brake_extending:
            yield {
                'name': 'Brake Deploy',
                'percent': round(
                    self.gravity_brake_position / self.gravity_brake_deployed_position * 100
                ),
            }
        elif self.gravity_brake_retracting:
            yield {
                'name': 'Brake Retract',
                'percent': round(
                    (self.gravity_brake_deployed_position - self.gravity_brake_position) / self.gravity_brake_deployed_position * 100
                ),
            }


    def use_battery_power(self, quantity: int) -> None:
        if quantity > self.battery_power:
            raise InsufficientPowerError
        self.battery_power -= quantity

    def charge_battery(self, quantity: int) -> None:
        self.battery_power = min(
            self.battery_capacity,
            self.battery_power + quantity,
        )

    def use_fuel(self, quantity: int) -> None:
        if quantity > self.fuel_level:
            raise InsufficientFuelError
        self.fuel_level -= quantity


    def adjust_resources(self, fps: int, game_frame: int):

        ''' ENERGY BEAM '''
        if self.ebeam_charging:
            adj = max(1, round(self.ebeam_charge_rate_per_second / fps))
            try:
                self.use_battery_power(round(adj * self.ebeam_charge_power_draw_multiple))
            except InsufficientPowerError:
                self.ebeam_charging = False
            else:
                self.ebeam_charge = min(
                    self.ebeam_charge + adj,
                    self.ebeam_charge_capacity,
                )
            if self.ebeam_charge >= self.ebeam_charge_capacity:
                self.ebeam_charging = False


        ''' Scanner POWER DRAW (RUNNING) '''
        if self.scanner_online:
            try:
                self.use_battery_power(
                    max(
                        round(self.scanner_idle_power_requirement_per_second / fps),
                        1,
                    )
                )
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
                            max(
                                round(self.scanner_get_lock_power_requirement_per_second / fps),
                                1,
                            ),
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
                        max(
                            round(self.scanner_idle_power_requirement_per_second / fps),
                            1,
                        )
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
                    round(self.scanner_activation_power_required_per_second / fps),
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
                        max(
                            round(self.engine_idle_power_requirement_per_second / fps),
                            1,
                        )
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
                    round(self.engine_activation_power_required_per_second / fps),
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
                    max(
                        round(self.engine_idle_power_requirement_per_second / fps),
                        1,
                    )
                )
            except InsufficientPowerError:
                self.engine_online = False

        elif self.engine_lit:
            ''' ENGINE POWER GENERATION & FUEL CONSUMPTION (LIT) '''
            try:
                self.use_fuel(
                    max(
                        round(self.engine_fuel_usage_per_second / fps),
                        1,
                    )
                )
            except InsufficientFuelError:
                # Flame out.
                self.engine_lit = False
                self.engine_online = False
                self.engine_boosting = False
            else:
                self.charge_battery(
                    max(
                        round(self.engine_battery_charge_per_second / fps),
                        1,
                    )
                )

            if self.engine_boosting:
                self.engine_boosting = False
                try:
                    self.use_fuel(
                        max(
                            round(self.engine_fuel_usage_per_second / fps) * self.engine_boost_multiple,
                            1,
                        )
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
                adj = max(
                    round(self.apu_activation_power_required_per_second / fps),
                    1,
                )
                try:
                    self.use_battery_power(adj)
                except InsufficientPowerError:
                    self.apu_starting = False
                else:
                    self.apu_startup_power_used += adj

        elif self.apu_online:
            try:
                self.use_fuel(
                    max(
                        round(self.apu_fuel_usage_per_second / fps),
                        1,
                    )
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
            return False
        self.ebeam_charge = round(self.ebeam_charge - delta_ebeam_charge)
        return True

    def advance_damage_properties(self, game_frame: int, map_x: int, map_y: int, fps: int) -> Optional[Tuple]:
        if self.died_on_frame is None:
            if self.coord_x < 0 or self.coord_y < 0 or self.coord_x > map_x or self.coord_y > map_y:
                self.die(game_frame)
                self.explode()
                return ShipDeathType.EXPLOSION, game_frame - self.died_on_frame

        elif self.explosion_frame:
            if self.explosion_frame < 200:
                # Ship is exploding, advance explosion frame
                self.explosion_frame += 1
                return ShipDeathType.EXPLOSION, game_frame - self.died_on_frame
            return ShipDeathType.ADRIFT, game_frame - self.died_on_frame

        elif self.explode_immediately:
            self.explode()
            return ShipDeathType.EXPLOSION, game_frame - self.died_on_frame

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
                return ShipDeathType.EXPLOSION, game_frame - self.died_on_frame
            return ShipDeathType.AFLAME, game_frame - self.died_on_frame

    def explode(self):
        self.explosion_frame = 1
        self.explosion_point = self.coords
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
            self._set_heading(self.scanner_data[self.scanner_lock_target]["relative_heading"])

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

        elif command == ShipCommands.DISABLE_AUTO_PILOT:
            self.cmd_disable_autopilot()

        elif command == ShipCommands.EXTEND_GRAVITY_BRAKE:
            self.cmd_extend_gravity_brake()
        elif command == ShipCommands.RETRACT_GRAVITY_BRAKE:
            self.cmd_retract_gravity_brake()

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
        delta_degrees = utils2d.heading_to_delta_heading_from_zero(self.heading)
        delta_radians = utils2d.degrees_to_radians(delta_degrees)

        self.rel_rot_coord_0 = utils2d.rotate(
            constants.ORGIN_COORD,
            self.heading_0_rel_coord_0,
            delta_radians
        )
        self.rel_rot_coord_1 = utils2d.rotate(
            constants.ORGIN_COORD,
            self.heading_0_rel_coord_1,
            delta_radians
        )
        self.rel_rot_coord_2 = utils2d.rotate(
            constants.ORGIN_COORD,
            self.heading_0_rel_coord_2,
            delta_radians
        )
        self.rel_rot_coord_3 = utils2d.rotate(
            constants.ORGIN_COORD,
            self.heading_0_rel_coord_3,
            delta_radians
        )

        self.fin_0_rel_rot_coord_0 = utils2d.rotate(
            constants.ORGIN_COORD,
            self.heading_0_fin_0_rel_coord_0,
            delta_radians
        )
        self.fin_0_rel_rot_coord_1 = utils2d.rotate(
            constants.ORGIN_COORD,
            self.heading_0_fin_0_rel_coord_1,
            delta_radians
        )
        self.fin_1_rel_rot_coord_0 = utils2d.rotate(
            constants.ORGIN_COORD,
            self.heading_0_fin_1_rel_coord_0,
            delta_radians
        )
        self.fin_1_rel_rot_coord_1 = utils2d.rotate(
            constants.ORGIN_COORD,
            self.heading_0_fin_1_rel_coord_1,
            delta_radians
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
        self.scanner_data.clear()

    def cmd_set_scanner_mode_radar(self) -> None:
        self.scanner_mode = ShipScannerMode.RADAR

    def cmd_set_scanner_mode_ir(self) -> None:
        self.scanner_mode = ShipScannerMode.IR

    def cmd_set_scanner_lock_target(self, target_id: str) -> None:
        if not self.scanner_online or self.scanner_locking:
            return
        if target_id not in self.scanner_data:
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

    def cmd_disable_autopilot(self):
        if self.autopilot_program:
            if self.autopilot_program == AutoPilotPrograms.POSITION_HOLD:
                self.engine_lit = False
            self.autopilot_program = None

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
