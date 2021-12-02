
import datetime as dt
from decimal import Decimal
from typing import Tuple, Dict, TypedDict, Optional, Generator, List

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
    SET_HEADING = 'set_heading'

    ACTIVATE_REACTION_WHEEL = 'activate_reaction_wheel'
    DEACTIVATE_REACTION_WHEEL = 'deactivate_reaction_wheel'

    ACTIVATE_ENGINE = 'activate_engine'
    DEACTIVATE_ENGINE = 'deactivate_engine'
    LIGHT_ENGINE = 'light_engine'
    UNLIGHT_ENGINE = 'unlight_engine'

    ACTIVATE_SCANNER = 'activate_scanner'
    DEACTIVATE_SCANNER = 'deactivate_scanner'
    SET_SCANNER_MODE_RADAR = 'set_scanner_mode_radar'
    SET_SCANNER_MODE_IR = 'set_scanner_mode_ir'

    ACTIVATE_AUTO_PILOT = 'activate_autopilot'
    DEACTIVATE_AUTO_PILOT = 'deactivate_autopilot'

class ShipStateKey:
    MASS = 'mass'

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
    designator: str
    element_type: str
    thermal_signature: Optional[int]
    coord_x: int
    coord_y: int
    relative_heading: int
    distance: int

    visual_fill_color: Optional[str]
    visual_stroke_color: Optional[str]
    visual_shape: Optional[str]     # 'arc' or 'rect'
    visual_radius: Optional[int]    # arc
    visual_p0: Optional[Tuple[int]] # rect
    visual_p1: Optional[Tuple[int]] #
    visual_p2: Optional[Tuple[int]] #
    visual_p3: Optional[Tuple[int]]  #
    visual_polygon_points: Optional[List[Tuple]]
    visual_engine_lit: Optional[bool] #


class TimerItem(TypedDict):
    name: str
    percent: int


class AutoPilotPrograms:
    HEADING_LOCKED_TARGET = 'heading_locked_target'
    POSITION_HOLD = 'position_hold'


class Ship(BaseModel):
    def __init__(self):
        super().__init__()

        self.game_frame = None

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
        self.engine_starting = False
        self.engine_startup_power_used = None
        self.engine_idle_power_requirement_per_second = None
        self.engine_seconds_to_activate = None
        self.engine_activation_power_required_total = None
        self.engine_activation_power_required_per_second = None
        self.engine_fuel_usage_per_second = None
        self.engine_battery_charge_per_second = None

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

        # Ship reaction wheel
        self.activate_reaction_wheel_power_requirement = None
        self.reaction_wheel_power_required_per_second = None
        self.reaction_wheel_online = False

        self.autopilot_program = None

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
    def engine_heading(self) -> int:
        return (self.heading - 180) if self.heading >= 180 else (self.heading + 180)

    @property
    def scanner_range(self):
        return self.scanner_radar_range if self.scanner_mode == ShipScannerMode.RADAR else self.scanner_ir_range

    def to_dict(self) -> Dict:
        """ Get JSON serializable representation of the ship.
        """
        return {
            'id': self.id,
            'available_commands': list(self.get_available_commands()),
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
            'reaction_wheel_online': self.reaction_wheel_online,

            'engine_newtons': self.engine_newtons,
            'engine_online': self.engine_online,
            'engine_lit': self.engine_lit,
            'engine_starting': self.engine_starting,

            'scanner_online': self.scanner_online,
            'scanner_starting': self.scanner_starting,
            'scanner_mode': self.scanner_mode,
            'scanner_radar_range': self.scanner_radar_range,
            'scanner_ir_range': self.scanner_ir_range,
            'scanner_ir_minimum_thermal_signature': self.scanner_ir_minimum_thermal_signature,
            'scanner_data': self.scanner_data,
            'scanner_thermal_signature': self.scanner_thermal_signature,

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

        instance.reaction_wheel_power_required_per_second = constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_SECOND
        instance.activate_reaction_wheel_power_requirement = constants.ACTIVATE_REACTION_WHEEL_POWER_REQUIREMENT

        instance.engine_mass = constants.ENGINE_MASS
        instance.engine_newtons = constants.ENGINE_BASE_FORCE_N
        instance.engine_seconds_to_activate = constants.SECONDS_TO_START_ENGINE
        instance.engine_activation_power_required_total = constants.ACTIVATE_ENGINE_POWER_REQUIREMENT_TOTAL
        instance.engine_activation_power_required_per_second = constants.ACTIVATE_ENGINE_POWER_REQUIREMENT_PER_SECOND
        instance.engine_idle_power_requirement_per_second = constants.ENGINE_IDLE_POWER_REQUIREMENT_PER_SECOND
        instance.engine_fuel_usage_per_second = constants.ENGINE_FUEL_USAGE_PER_SECOND
        instance.engine_battery_charge_per_second = constants.ENGINE_BATTERY_CHARGE_PER_SECOND

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


    def calculate_damage(self):
        pass


    def adjust_resources(self, fps: int):
        ''' REACTION WHEEL '''
        if self.reaction_wheel_online:
            try:
                self.use_battery_power(
                    max(
                        round(self.reaction_wheel_power_required_per_second / fps),
                        1,
                    )
                )
            except InsufficientPowerError:
                self.reaction_wheel_online = False

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
            else:
                self.charge_battery(
                    max(
                        round(self.engine_battery_charge_per_second / fps),
                        1,
                    )
                )


    def calculate_physics(self, fps: int) -> None:
        if self.engine_lit:
            adj_meters_per_second = float(self.engine_newtons / self.mass)
            adj_meters_per_frame = float(adj_meters_per_second / fps)

            delta_x, delta_y = utils2d.calculate_x_y_components(
                adj_meters_per_frame,
                self.heading,
            )
            self.velocity_x_meters_per_second += delta_x
            self.velocity_y_meters_per_second += delta_y

        if self.velocity_x_meters_per_second == 0 and self.velocity_y_meters_per_second == 0:
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


    def calculate_side_effects(self):
        pass


    def get_available_commands(self) -> Generator[str, None, None]:
        # Reaction Wheel
        if not self.reaction_wheel_online:
            yield ShipCommands.ACTIVATE_REACTION_WHEEL
        else:
            yield ShipCommands.DEACTIVATE_REACTION_WHEEL

        # Engine
        if not self.engine_starting:
            if not self.engine_online:
                yield ShipCommands.ACTIVATE_ENGINE
            else:
                if self.engine_lit:
                    yield ShipCommands.UNLIGHT_ENGINE
                else:
                    yield ShipCommands.LIGHT_ENGINE
                    yield ShipCommands.DEACTIVATE_ENGINE

        # Scanner
        if not self.scanner_starting:
            if not self.scanner_online:
                yield ShipCommands.ACTIVATE_SCANNER
            else:
                yield ShipCommands.DEACTIVATE_SCANNER
        yield (
            ShipCommands.SET_SCANNER_MODE_RADAR
            if self.scanner_mode == ShipScannerMode.IR
            else ShipCommands.SET_SCANNER_MODE_IR
        )



    def process_command(self, command: str, *args, **kwargs):
        if command == ShipCommands.SET_HEADING:
            return self.cmd_set_heading(args[0])

        elif command == ShipCommands.ACTIVATE_REACTION_WHEEL:
            self.cmd_set_reaction_wheel_status(True)
        elif command == ShipCommands.DEACTIVATE_REACTION_WHEEL:
            self.cmd_set_reaction_wheel_status(False)

        elif command == ShipCommands.ACTIVATE_ENGINE:
            self.cmd_activate_engine()
        elif command == ShipCommands.DEACTIVATE_ENGINE:
            self.cmd_deactivate_engine()
        elif command == ShipCommands.LIGHT_ENGINE:
            self.cmd_light_engine()
        elif command == ShipCommands.UNLIGHT_ENGINE:
            self.cmd_unlight_engine()
        elif command == ShipCommands.ACTIVATE_SCANNER:
            self.cmd_activate_scanner()
        elif command == ShipCommands.DEACTIVATE_SCANNER:
            self.cmd_deactivate_scanner()
        elif command == ShipCommands.SET_SCANNER_MODE_RADAR:
            self.cmd_set_scanner_mode_radar()
        elif command == ShipCommands.SET_SCANNER_MODE_IR:
            self.cmd_set_scanner_mode_ir()
        else:
            raise ShipCommandError("NotImplementedError")

    # Reaction Wheel Commands.
    def cmd_set_reaction_wheel_status(self, set_online: bool):
        if set_online:
            if self.reaction_wheel_online:
                return
            try:
                self.use_battery_power(
                    self.activate_reaction_wheel_power_requirement
                )
            except InsufficientPowerError:
                return
            else:
                self.reaction_wheel_online = True
        else:
            self.reaction_wheel_online = False

    def cmd_set_heading(self, heading: int):
        if heading == self.heading:
            return
        if not self.reaction_wheel_online:
            return
        if not (359 >= heading >= 0):
            raise ShipCommandError("invalid heading")

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
        self.scanner_locking_power_used = 0
        self.scanner_lock_target = target_id


