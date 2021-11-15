
from decimal import Decimal
from typing import Tuple, Dict, TypedDict, Optional

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

    ACTIVATE_SCANNER = 'activate_scanner'
    DEACTIVATE_SCANNER = 'deactivate_scanner'
    SET_SCANNER_MODE_RADAR = 'set_scanner_mode_radar'
    SET_SCANNER_MODE_IR = 'set_scanner_mode_ir'


class ShipStateKey:
    MASS = 'mass'


class ShipScannerMode:
    RADAR = 'radar'
    IR = 'ir'


class ScannedElement(TypedDict):
    designator: str
    diameter_meters: Optional[int]
    thermal_signature: Optional[int]
    coord_x: int
    coord_y: int
    relative_heading: int
    distance: int


class Ship(BaseModel):
    def __init__(self):
        super().__init__()

        self.game_frame = None

        self.map_units_per_meter = None

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

        # relative coordinate boundaries of the ship with heading fixed to zero.
        # These coords will NOT change unless the ship size changes
        self.heading_0_rel_coord_0 = (None, None,)
        self.heading_0_rel_coord_1 = (None, None,)
        self.heading_0_rel_coord_2 = (None, None,)
        self.heading_0_rel_coord_3 = (None, None,)

        # </END OF RELATIVE COORDINATES>

        # Velocity
        self.velocity_x_meters_per_second = float(0)
        self.velocity_y_meters_per_second = float(0)


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
        self.engine_start_complete_at_frame = None
        self.engine_idle_power_requirement_per_frame = None
        self.engine_frames_to_activate = None
        self.engine_activation_power_required_total = None
        self.engine_activation_power_required_per_frame = None
        self.engine_fuel_usage_per_frame = None
        self.engine_battery_charge_per_frame = None

        # Scanner
        self.scanner_designator = None # A unique "human readable" identifier used to identify this ship on other ships' scanners
        self.scanner_online = False
        self.scanner_starting = False
        self.scanner_start_complete_at_frame = None
        self.scanner_mode = None
        self.scanner_radar_range = None
        self.scanner_ir_range = None
        self.scanner_ir_minimum_thermal_signature = None
        self.scanner_idle_power_requirement_per_frame = None
        self.scanner_frames_to_activate = None
        self.scanner_activation_power_required_total = None
        self.scanner_activation_power_required_per_frame = None
        self.scanner_data: Dict[str, ScannedElement] = {}
        # Size of the ship on an enemies RADAR mode scanner
        self.scanner_diameter = None
        # Temperature of the ship as it appears on an enemies' IR mode scanner1
        self.scanner_thermal_signature = None


        # Ship reaction wheel
        self.reaction_wheel_online = False

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

    def refresh_scanner_diameter(self):
        # This method should be called when the ship's physical dimentions change
        d1 = self.h0_x2 - self.h0_x1
        d2 = self.h0_y2 - self.h0_y1
        self.scanner_diameter = round((d1 + d2) / 2)

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

    @classmethod
    def spawn(cls, map_units_per_meter: int = 1) -> "Ship":
        """ Create new unpositioned ship with defaults
        """
        instance = cls()

        instance.map_units_per_meter = map_units_per_meter

        x_len = constants.SHIP_X_LEN * map_units_per_meter
        y_len = constants.SHIP_Y_LEN * map_units_per_meter

        x1 = (x_len / 2) * -1
        x2 = (x_len / 2)
        y1 = (y_len / 2) * -1
        y2 = (y_len / 2)

        instance.heading_0_rel_coord_0 = (x1, y1,)
        instance.heading_0_rel_coord_1 = (x1, y2,)
        instance.heading_0_rel_coord_2 = (x2, y2,)
        instance.heading_0_rel_coord_3 = (x2, y1,)
        instance.refresh_scanner_diameter()

        instance.rel_rot_coord_0 = (x1, y1,)
        instance.rel_rot_coord_1 = (x1, y2,)
        instance.rel_rot_coord_2 = (x2, y2,)
        instance.rel_rot_coord_3 = (x2, y1,)

        instance.battery_power = constants.BATTERY_STARTING_POWER
        instance.battery_capacity = constants.BATTERY_POWER_CAPACITY
        instance.battery_mass = constants.BATTERY_MASS

        instance.fuel_level = constants.FUEL_START_LEVEL
        instance.fuel_capacity = constants.FUEL_CAPACITY

        instance.engine_mass = constants.ENGINE_MASS
        instance.engine_newtons = constants.ENGINE_BASE_FORCE_N
        instance.engine_frames_to_activate = constants.FRAMES_TO_START_ENGINE
        instance.engine_activation_power_required_total = constants.ACTIVATE_ENGINE_POWER_REQUIREMENT_TOTAL
        instance.engine_activation_power_required_per_frame = constants.ACTIVATE_ENGINE_POWER_REQUIREMENT_PER_FRAME
        instance.engine_idle_power_requirement_per_frame = constants.ENGINE_IDLE_POWER_REQUIREMENT_PER_FRAME
        instance.engine_fuel_usage_per_frame = constants.ENGINE_FUEL_USAGE_PER_FRAME
        instance.engine_battery_charge_per_frame = constants.ENGINE_BATTERY_CHARGE_PER_FRAME

        instance.scanner_mode = ShipScannerMode.RADAR
        instance.scanner_radar_range = constants.SCANNER_MODE_RADAR_RANGE_M
        instance.scanner_ir_range = constants.SCANNER_MODE_IR_RANGE_M
        instance.scanner_ir_minimum_thermal_signature = constants.SCANNER_IR_MINIMUM_THERMAL_SIGNATURE
        instance.scanner_idle_power_requirement_per_frame = constants.SCANNER_POWER_REQUIREMENT_PER_FRAME
        instance.scanner_frames_to_activate = constants.FRAMES_TO_START_SCANNER
        instance.scanner_activation_power_required_total = constants.ACTIVATE_SCANNER_POWER_REQUIREMENT_TOTAL
        instance.scanner_activation_power_required_per_frame = constants.ACTIVATE_ENGINE_POWER_REQUIREMENT_PER_FRAME
        instance.scanner_thermal_signature = 0

        return instance


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


    def adjust_resources(self):
        ''' REACTION WHEEL '''
        if self.reaction_wheel_online:
            try:
                self.use_battery_power(
                    constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME
                )
            except InsufficientPowerError:
                self.reaction_wheel_online = False

        ''' Scanner POWER DRAW (RUNNING) '''
        if self.scanner_online:
            try:
                self.use_battery_power(
                    self.scanner_idle_power_requirement_per_frame
                )
            except InsufficientPowerError:
                self.scanner_online = False

        elif self.scanner_starting:
            ''' Scanner POWER DRAW (STARTING) '''
            startup_complete = self.scanner_start_complete_at_frame <= self.game_frame
            if startup_complete:
                self.scanner_starting = False
                self.scanner_start_complete_at_frame = None
                try:
                    self.use_battery_power(
                        self.scanner_idle_power_requirement_per_frame
                    )
                except InsufficientPowerError:
                    # Scanner startup complete but not enough power to idle scanner
                    pass
                else:
                    # Scanner Startup successful.
                    self.scanner_online = True

            else:
                # continue scanner startup
                try:
                    self.use_battery_power(
                        self.scanner_activation_power_required_per_frame
                    )
                except InsufficientPowerError:
                    # Cancel startup, not enough power.
                    self.scanner_starting = False
                    self.scanner_start_complete_at_frame = None



        ''' ENGINE POWER DRAW (STARTING) # # # '''
        if self.engine_starting:
            startup_complete = self.engine_start_complete_at_frame <= self.game_frame
            if startup_complete:
                self.engine_starting = False
                self.engine_start_complete_at_frame = None
                try:
                    self.use_battery_power(
                        self.engine_idle_power_requirement_per_frame
                    )
                except InsufficientPowerError:
                    # Engine startup complete but not enough power to idle engine.
                    pass
                else:
                    # Engine Startup successful.
                    self.engine_online = True
            else:
                # Continue engine startup.
                try:
                    self.use_battery_power(
                        self.engine_activation_power_required_per_frame
                    )
                except InsufficientPowerError:
                    # Cancel startup, not enough power.
                    self.engine_starting = False
                    self.engine_start_complete_at_frame = None

        elif self.engine_online and not self.engine_lit:
            ''' ENGINE POWER DRAW (IDLE) '''
            try:
                self.use_battery_power(
                    constants.ENGINE_IDLE_POWER_REQUIREMENT_PER_FRAME
                )
            except InsufficientPowerError:
                self.engine_online = False

        elif self.engine_lit:
            ''' ENGINE POWER GENERATION & FUEL CONSUMPTION (LIT) '''
            try:
                self.use_fuel(self.engine_fuel_usage_per_frame)
            except InsufficientFuelError:
                # Flame out.
                self.engine_lit = False
                self.engine_online = False
            else:
                self.charge_battery(
                    self.engine_battery_charge_per_frame,
                )


    def calculate_physics(self, frames_per_second: int) -> None:
        if self.engine_lit:
            adj_meters_per_second = float(self.engine_newtons / self.mass)
            adj_meters_per_frame = float(adj_meters_per_second / frames_per_second)

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
        distance_map_units = round((distance_meters * self.map_units_per_meter) / frames_per_second)

        self.coord_x, self.coord_y = utils2d.translate_point(
            (self.coord_x, self.coord_y),
            heading,
            distance_map_units,
        )


    def calculate_side_effects(self):
        pass


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


    def cmd_set_reaction_wheel_status(self, is_online: bool):
        if is_online:
            if self.reaction_wheel_online:
                return
            try:
                self.use_battery_power(
                    constants.ACTIVATE_REACTION_WHEEL_POWER_REQUIREMENT
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

    def cmd_activate_engine(self) -> None:
        if self.engine_online:
            return
        if self.engine_starting:
            return
        self.engine_starting = True
        self.engine_start_complete_at_frame = self.game_frame + self.engine_frames_to_activate

    def cmd_deactivate_engine(self) -> None:
        if not self.engine_online:
            return
        self.engine_lit = False
        self.engine_online = False

    def cmd_light_engine(self) -> None:
        if not self.engine_online or self.engine_lit:
            return
        self.engine_lit = True


    def cmd_activate_scanner(self) -> None:
        if self.scanner_online or self.scanner_starting:
            return
        self.scanner_starting = True
        self.scanner_start_complete_at_frame = self.game_frame + self.scanner_frames_to_activate

    def cmd_deactivate_scanner(self) -> None:
        if not self.scanner_online or self.scanner_starting:
            return
        self.scanner_online = False
        self.scanner_data.clear()

    def cmd_set_scanner_mode_radar(self) -> None:
        self.scanner_mode = ShipScannerMode.RADAR

    def cmd_set_scanner_mode_ir(self) -> None:
        self.scanner_mode = ShipScannerMode.IR
