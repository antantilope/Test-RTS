
from unittest import TestCase
from uuid import uuid4

from api.models.ship import ShipStateKey
from api import constants
from .utils import (
    DebugShip as Ship,
    TEST_ORIGIN,
    assert_floats_equal,
    assert_coord_in_quadrant,
    assert_ship_moves_from_quadrant_to_quadrant,
    PROFILE_INCREASE,
    PROFILE_DECREASE,
    PROFILE_NO_CHANGE,
)



'''
 █████  ██████       ██ ██    ██ ███████ ████████
██   ██ ██   ██      ██ ██    ██ ██         ██
███████ ██   ██      ██ ██    ██ ███████    ██
██   ██ ██   ██ ██   ██ ██    ██      ██    ██
██   ██ ██████   █████   ██████  ███████    ██

██████  ███████ ███████  ██████  ██    ██ ██████   ██████ ███████ ███████
██   ██ ██      ██      ██    ██ ██    ██ ██   ██ ██      ██      ██
██████  █████   ███████ ██    ██ ██    ██ ██████  ██      █████   ███████
██   ██ ██           ██ ██    ██ ██    ██ ██   ██ ██      ██           ██
██   ██ ███████ ███████  ██████   ██████  ██   ██  ██████ ███████ ███████
'''


class TestShipAdjustResources(TestCase):
    def setUp(self):
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=10)
        self.ship.reaction_wheel_online = False

    def test_battery_power_reduced_if_reaction_wheel_online(self):
        ''' REACTION WHEEL '''
        self.ship.reaction_wheel_online = True
        start_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_power - constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME
        assert self.ship.reaction_wheel_online

    def test_battery_power_not_reduced_if_reaction_wheel_offline(self):
        ''' REACTION WHEEL '''
        self.ship.reaction_wheel_online = False
        start_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_power
        assert not self.ship.reaction_wheel_online

    def test_reaction_wheel_disabled_if_battery_runs_out_of_power(self):
        ''' REACTION WHEEL '''
        self.ship.reaction_wheel_online = True

        # Enough power to run the reaction wheel for 3 frames
        self.ship.battery_power = constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 3

        self.ship.adjust_resources()
        assert self.ship.battery_power == constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 2
        assert self.ship.reaction_wheel_online

        self.ship.adjust_resources()
        assert self.ship.battery_power == constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 1
        assert self.ship.reaction_wheel_online

        self.ship.adjust_resources()
        assert self.ship.battery_power == constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 0
        assert self.ship.reaction_wheel_online

        self.ship.adjust_resources() # No battery power to run reaction wheel.
        assert self.ship.battery_power == constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 0
        assert not self.ship.reaction_wheel_online # Reaction wheel disabled.


    def test_engine_start_process_uses_power(self):
        ''' ENGINE ACTIVATE '''
        self.ship.game_frame = 1
        self.ship.engine_starting = True
        self.ship.engine_start_complete_at_frame = 3
        start_battery_power = self.ship.battery_power
        power_usage_per_frame_eng_start = self.ship.engine_activation_power_required_per_frame

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 1
        assert not self.ship.engine_online
        assert self.ship.engine_starting
        assert self.ship.engine_start_complete_at_frame is not None

        self.ship.game_frame = 2
        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 2
        assert not self.ship.engine_online
        assert self.ship.engine_starting
        assert self.ship.engine_start_complete_at_frame is not None

        self.ship.game_frame = 3
        self.ship.adjust_resources()
        assert self.ship.battery_power == (
            start_battery_power - (
                power_usage_per_frame_eng_start * 2
                + self.ship.engine_idle_power_requirement_per_frame
            )
        )
        assert self.ship.engine_online
        assert not self.ship.engine_lit
        assert not self.ship.engine_starting
        assert self.ship.engine_start_complete_at_frame is None

    def test_engine_start_process_fails_if_not_enough_power(self):
        ''' ENGINE ACTIVATE '''
        self.ship.game_frame = 1
        self.ship.engine_starting = True
        self.ship.engine_start_complete_at_frame = 3
        start_battery_power = self.ship.battery_power
        power_usage_per_frame_eng_start = self.ship.engine_activation_power_required_per_frame

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 1
        assert not self.ship.engine_online
        assert self.ship.engine_starting
        assert self.ship.engine_start_complete_at_frame is not None

        self.ship.game_frame = 2
        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 2
        assert not self.ship.engine_online
        assert self.ship.engine_starting
        assert self.ship.engine_start_complete_at_frame is not None

        self.ship.game_frame = 3
        self.ship.battery_power = 0
        self.ship.adjust_resources()
        assert not self.ship.engine_online
        assert not self.ship.engine_lit
        assert not self.ship.engine_starting
        assert self.ship.engine_start_complete_at_frame is None

    def test_idle_engine_uses_power(self):
        ''' ENGINE IDLE '''
        self.ship.engine_online = True
        starting_fuel = self.ship.fuel_level
        starting_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.battery_power == starting_power - self.ship.engine_idle_power_requirement_per_frame * 1
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

        self.ship.adjust_resources()
        assert self.ship.battery_power == starting_power - self.ship.engine_idle_power_requirement_per_frame * 2
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

    def test_idle_engine_deactivates_if_not_enough_power(self):
        ''' ENGINE IDLE '''
        self.ship.engine_online = True
        starting_fuel = self.ship.fuel_level
        starting_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.battery_power == starting_power - self.ship.engine_idle_power_requirement_per_frame * 1
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

        # Not enough power to idle the engine for another frame
        self.ship.battery_power = self.ship.engine_idle_power_requirement_per_frame - 1
        self.ship.adjust_resources()
        assert self.ship.battery_power == (self.ship.engine_idle_power_requirement_per_frame - 1)
        assert self.ship.fuel_level == starting_fuel
        assert not self.ship.engine_online

    def test_lit_engine_uses_fuel_and_generates_power(self):
        ''' ENGINE LIT '''
        self.ship.engine_online = True
        self.ship.engine_lit = True
        start_fuel = self.ship.fuel_level
        start_power = self.ship.battery_power
        fuel_usage_per_frame = self.ship.engine_fuel_usage_per_frame
        power_gen_per_frame = self.ship.engine_battery_charge_per_frame

        self.ship.adjust_resources()
        assert self.ship.fuel_level == start_fuel - fuel_usage_per_frame * 1
        assert self.ship.battery_power == start_power + power_gen_per_frame * 1
        assert self.ship.engine_online
        assert self.ship.engine_lit

        self.ship.adjust_resources()
        assert self.ship.fuel_level == start_fuel - fuel_usage_per_frame * 2
        assert self.ship.battery_power == start_power + power_gen_per_frame * 2
        assert self.ship.engine_online
        assert self.ship.engine_lit

    def test_lit_engine_flames_out_if_not_enough_fuel(self):
        ''' ENGINE LIT '''
        self.ship.engine_online = True
        self.ship.engine_lit = True
        fuel_usage_per_frame = self.ship.engine_fuel_usage_per_frame
        power_gen_per_frame = self.ship.engine_battery_charge_per_frame

        # Enough fuel for exactly 1 frame
        self.ship.fuel_level = round(fuel_usage_per_frame * 1.5)
        start_fuel = self.ship.fuel_level
        start_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.fuel_level == start_fuel - fuel_usage_per_frame * 1
        assert self.ship.battery_power == start_power + power_gen_per_frame * 1
        assert self.ship.engine_online
        assert self.ship.engine_lit

        # Flame out
        self.ship.adjust_resources()
        assert self.ship.fuel_level == start_fuel - fuel_usage_per_frame * 1
        assert self.ship.battery_power == start_power + power_gen_per_frame * 1
        assert not self.ship.engine_online
        assert not self.ship.engine_lit


    def test_scanner_start_process_uses_power(self):
        ''' SCANNER ACTIVATE '''
        start_power = self.ship.battery_power
        self.ship.game_frame = 1
        self.ship.scanner_start_complete_at_frame = 3
        self.ship.scanner_online = False
        self.ship.scanner_starting = True

        self.ship.adjust_resources()
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - (self.ship.scanner_activation_power_required_per_frame * 1)

        self.ship.game_frame = 2
        self.ship.adjust_resources()
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - (self.ship.scanner_activation_power_required_per_frame * 2)

        # Startup Complete on this frame.
        self.ship.game_frame = 3
        self.ship.adjust_resources()
        assert not self.ship.scanner_starting
        assert self.ship.scanner_online
        assert self.ship.battery_power == start_power - (
            (self.ship.scanner_activation_power_required_per_frame * 2) + (self.ship.scanner_idle_power_requirement_per_frame * 1)
        )
        # Scanner is idling
        self.ship.adjust_resources()
        assert not self.ship.scanner_starting
        assert self.ship.scanner_online
        assert self.ship.battery_power == start_power - (
            (self.ship.scanner_activation_power_required_per_frame * 2) + (self.ship.scanner_idle_power_requirement_per_frame * 2)
        )

    def test_scanner_start_process_fails_if_not_enough_power(self):
        ''' SCANNER ACTIVATE '''
        self.ship.game_frame = 1
        self.ship.scanner_start_complete_at_frame = 5
        self.ship.scanner_online = False
        self.ship.scanner_starting = True
        self.ship.battery_power = self.ship.scanner_activation_power_required_per_frame * 3
        start_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - (self.ship.scanner_activation_power_required_per_frame * 1)

        self.ship.game_frame += 1
        self.ship.adjust_resources()
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - (self.ship.scanner_activation_power_required_per_frame * 2)

        self.ship.game_frame += 1
        self.ship.adjust_resources()
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == 0

        # No more power
        self.ship.game_frame += 1
        self.ship.adjust_resources()
        assert not self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == 0

    def test_idle_scanner_uses_power(self):
        ''' SCANNER IDLE '''
        self.ship.game_frame = 1
        self.ship.scanner_online = True
        self.ship.battery_power = self.ship.scanner_idle_power_requirement_per_frame * 20
        start_power = self.ship.battery_power

        for i in range(10):
            self.ship.adjust_resources()
            assert not self.ship.scanner_starting
            assert self.ship.scanner_online
            assert self.ship.battery_power == start_power - (self.ship.scanner_idle_power_requirement_per_frame * (i  + 1))

    def test_idle_scanner_deactivates_if_not_enough_power(self):
        ''' SCANNER IDLE '''
        self.ship.scanner_online = True
        self.ship.battery_power = self.ship.scanner_idle_power_requirement_per_frame * 2
        start_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert not self.ship.scanner_starting
        assert self.ship.scanner_online
        assert self.ship.battery_power == start_power - (self.ship.scanner_idle_power_requirement_per_frame * 1)

        # Scanner will function this frame, but will drain last of battery power
        self.ship.adjust_resources()
        assert not self.ship.scanner_starting
        assert self.ship.scanner_online
        assert self.ship.battery_power == start_power - (self.ship.scanner_idle_power_requirement_per_frame * 2)
        assert self.ship.battery_power == 0

        # Scanner is deactivated this frame.
        self.ship.adjust_resources()
        assert not self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == 0


'''
 ██████  █████  ██       ██████ ██    ██ ██       █████  ████████ ███████
██      ██   ██ ██      ██      ██    ██ ██      ██   ██    ██    ██
██      ███████ ██      ██      ██    ██ ██      ███████    ██    █████
██      ██   ██ ██      ██      ██    ██ ██      ██   ██    ██    ██
 ██████ ██   ██ ███████  ██████  ██████  ███████ ██   ██    ██    ███████

██████  ██   ██ ██    ██ ███████ ██  ██████ ███████
██   ██ ██   ██  ██  ██  ██      ██ ██      ██
██████  ███████   ████   ███████ ██ ██      ███████
██      ██   ██    ██         ██ ██ ██           ██
██      ██   ██    ██    ███████ ██  ██████ ███████

'''


'''
                      __                      __    __
                     |  \                    |  \  |  \
 __     __   ______  | $$  ______    _______  \$$ _| $$_    __    __
|  \   /  \ /      \ | $$ /      \  /       \|  \|   $$ \  |  \  |  \
 \$$\ /  $$|  $$$$$$\| $$|  $$$$$$\|  $$$$$$$| $$ \$$$$$$  | $$  | $$
  \$$\  $$ | $$    $$| $$| $$  | $$| $$      | $$  | $$ __ | $$  | $$
   \$$ $$  | $$$$$$$$| $$| $$__/ $$| $$_____ | $$  | $$|  \| $$__/ $$
    \$$$    \$$     \| $$ \$$    $$ \$$     \| $$   \$$  $$ \$$    $$
     \$      \$$$$$$$ \$$  \$$$$$$   \$$$$$$$ \$$    \$$$$  _\$$$$$$$
                                                           |  \__| $$
                                                            \$$    $$
                                                             \$$$$$$
                     __
                    |  \
  ______   _______  | $$ __    __
 /      \ |       \ | $$|  \  |  \
|  $$$$$$\| $$$$$$$\| $$| $$  | $$
| $$  | $$| $$  | $$| $$| $$  | $$
| $$__/ $$| $$  | $$| $$| $$__/ $$
 \$$    $$| $$  | $$| $$ \$$    $$
  \$$$$$$  \$$   \$$ \$$ _\$$$$$$$
                        |  \__| $$
                         \$$    $$
                          \$$$$$$
'''

class TestShipCMDCalculatePhysics(TestCase):
    def setUp(self):
        self.map_units_per_meter = 10
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=self.map_units_per_meter)

        # Set values that are used in physics calculations.
        self.ship.engine_newtons = 1100
        self.ship._state[ShipStateKey.MASS] = 645
        self.fps = 2
        self._reset_ship()

    def _reset_ship(self):
        self.ship.coord_x = TEST_ORIGIN[0]
        self.ship.coord_y = TEST_ORIGIN[1]
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = 0
        self.start_x = self.ship.coord_x
        self.start_y = self.ship.coord_y

    def _calculate_physics(self) -> None:
        self.ship.calculate_physics(self.fps)


    ''' No Velocity and No Acceleration
    '''
    def test_ship_position_does_not_change_if_no_velocity_and_no_acceleration(self):
        self.ship.velocity_x_meters_per_second = 0 # No velocity
        self.ship.velocity_y_meters_per_second = 0 #
        self.ship.engine_lit = False               # No Acceleration

        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 0 # No change in velocity
        assert self.ship.velocity_y_meters_per_second == 0
        assert self.ship.coord_x == self.start_x # No change in position
        assert self.ship.coord_y == self.start_y


    ''' NO acceleration, only X or only Y velocity
    '''
    def test_ship_position_does_change_if_positive_x_velocity_and_no_acceleration(self):
        self.ship.velocity_x_meters_per_second = 240
        self.ship.velocity_y_meters_per_second = 0

        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 240
        assert self.ship.velocity_y_meters_per_second == 0
        assert self.ship.coord_x == self.start_x + 1200
        assert self.ship.coord_y == self.start_y

    def test_ship_position_does_change_if_negative_x_velocity_and_no_acceleration(self):
        self.ship.velocity_x_meters_per_second = -240
        self.ship.velocity_y_meters_per_second = 0

        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == -240
        assert self.ship.velocity_y_meters_per_second == 0
        assert self.ship.coord_x == self.start_x - 1200
        assert self.ship.coord_y == self.start_y

    def test_ship_position_does_change_if_positive_y_velocity_and_no_acceleration(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = 240

        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 0
        assert self.ship.velocity_y_meters_per_second == 240
        assert self.ship.coord_x == self.start_x
        assert self.ship.coord_y == self.start_y + 1200

    def test_ship_position_does_change_if_negative_y_velocity_and_no_acceleration(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = -240

        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 0
        assert self.ship.velocity_y_meters_per_second == -240
        assert self.ship.coord_x == self.start_x
        assert self.ship.coord_y == self.start_y - 1200


    ''' NO acceleration, X AND Y Velocity
    '''
    def test_ship_position_does_change_if_equal_positive_x_and_y_velocity(self):
        self.ship.velocity_x_meters_per_second = 240
        self.ship.velocity_y_meters_per_second = 240

        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 240
        assert self.ship.velocity_y_meters_per_second == 240
        assert self.ship.coord_x == self.start_x + 1200
        assert self.ship.coord_y == self.start_y + 1200

    def test_ship_position_does_change_if_equal_positive_x_and_negative_y_velocity(self):
        self.ship.velocity_x_meters_per_second = -240
        self.ship.velocity_y_meters_per_second = 240

        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == -240
        assert self.ship.velocity_y_meters_per_second == 240
        assert self.ship.coord_x == self.start_x - 1200
        assert self.ship.coord_y == self.start_y + 1200

    def test_ship_position_does_change_if_equal_negative_x_and_positive_y_velocity(self):
        self.ship.velocity_x_meters_per_second = 240
        self.ship.velocity_y_meters_per_second = -240

        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 240
        assert self.ship.velocity_y_meters_per_second == -240
        assert self.ship.coord_x == self.start_x + 1200
        assert self.ship.coord_y == self.start_y - 1200

    def test_ship_position_does_change_if_equal_negative_x_and_y_velocity(self):
        self.ship.velocity_x_meters_per_second = -240
        self.ship.velocity_y_meters_per_second = -240

        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == -240
        assert self.ship.velocity_y_meters_per_second == -240
        assert self.ship.coord_x == self.start_x - 1200
        assert self.ship.coord_y == self.start_y - 1200

    def test_ship_position_does_change_if_not_equal_positive_x_and_y_velocity(self):
        self.ship.velocity_x_meters_per_second = 50
        self.ship.velocity_y_meters_per_second = 300
        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 50
        assert self.ship.velocity_y_meters_per_second == 300
        assert self.ship.coord_x == self.start_x + 238
        assert self.ship.coord_y == self.start_y + 1502

        self._reset_ship()
        self.ship.velocity_x_meters_per_second = 300
        self.ship.velocity_y_meters_per_second = 50
        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 300
        assert self.ship.velocity_y_meters_per_second == 50
        assert self.ship.coord_x == self.start_x + 1502
        assert self.ship.coord_y == self.start_y + 238

    def test_ship_position_does_change_if_not_equal_negative_x_and_y_velocity(self):
        self.ship.velocity_x_meters_per_second = -50
        self.ship.velocity_y_meters_per_second = -300
        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == -50
        assert self.ship.velocity_y_meters_per_second == -300
        assert self.ship.coord_x == self.start_x - 238
        assert self.ship.coord_y == self.start_y - 1502

        self._reset_ship()
        self.ship.velocity_x_meters_per_second = -300
        self.ship.velocity_y_meters_per_second = -50
        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == -300
        assert self.ship.velocity_y_meters_per_second == -50
        assert self.ship.coord_x == self.start_x - 1502
        assert self.ship.coord_y == self.start_y - 238

    def test_ship_position_does_change_if_not_equal_positive_x_and_negative_y_velocity(self):
        self.ship.velocity_x_meters_per_second = 300
        self.ship.velocity_y_meters_per_second = -50
        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 300
        assert self.ship.velocity_y_meters_per_second == -50
        assert self.ship.coord_x == self.start_x + 1502
        assert self.ship.coord_y == self.start_y - 238

        self._reset_ship()
        self.ship.velocity_x_meters_per_second = 50
        self.ship.velocity_y_meters_per_second = -300
        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 50
        assert self.ship.velocity_y_meters_per_second == -300
        assert self.ship.coord_x == self.start_x + 238
        assert self.ship.coord_y == self.start_y - 1502

    def test_ship_position_does_change_if_not_equal_negative_x_and_positive_y_velocity(self):
        self.ship.velocity_x_meters_per_second = -300
        self.ship.velocity_y_meters_per_second = 50
        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == -300
        assert self.ship.velocity_y_meters_per_second == 50
        assert self.ship.coord_x == self.start_x - 1502
        assert self.ship.coord_y == self.start_y + 238

        self._reset_ship()
        self.ship.velocity_x_meters_per_second = -50
        self.ship.velocity_y_meters_per_second = 300
        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == -50
        assert self.ship.velocity_y_meters_per_second == 300
        assert self.ship.coord_x == self.start_x - 238
        assert self.ship.coord_y == self.start_y + 1502

    '''
                                        |  \                              |  \    |  \
  ______    _______   _______   ______  | $$  ______    ______   ______  _| $$_    \$$  ______   _______
 |      \  /       \ /       \ /      \ | $$ /      \  /      \ |      \|   $$ \  |  \ /      \ |       \
  \$$$$$$\|  $$$$$$$|  $$$$$$$|  $$$$$$\| $$|  $$$$$$\|  $$$$$$\ \$$$$$$\\$$$$$$  | $$|  $$$$$$\| $$$$$$$\
 /      $$| $$      | $$      | $$    $$| $$| $$    $$| $$   \$$/      $$ | $$ __ | $$| $$  | $$| $$  | $$
|  $$$$$$$| $$_____ | $$_____ | $$$$$$$$| $$| $$$$$$$$| $$     |  $$$$$$$ | $$|  \| $$| $$__/ $$| $$  | $$
 \$$    $$ \$$     \ \$$     \ \$$     \| $$ \$$     \| $$      \$$    $$  \$$  $$| $$ \$$    $$| $$  | $$
  \$$$$$$$  \$$$$$$$  \$$$$$$$  \$$$$$$$ \$$  \$$$$$$$ \$$       \$$$$$$$   \$$$$  \$$  \$$$$$$  \$$   \$$

    '''

    ''' ACCELERATION from 0 velocity along cardinal headings (N/S/E/W)
    '''
    def test_ship_position_accelerate_from_0_velocity_n(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = 0
        self.ship.heading = constants.DEGREES_NORTH
        self.ship.engine_lit = True

        # when ship is accelerating, delta velocity is linear and position change is exponential
        delta_velocity_per_frame = 0.8527131782945736

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 1)
        assert self.ship.coords == (self.start_x, 100_004)


        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 2)
        assert self.ship.coords == (self.start_x, 100_013)


        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 3)
        assert self.ship.coords == (self.start_x, 100_026)


        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 4)
        assert self.ship.coords == (self.start_x, 100_043)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 5)
        assert self.ship.coords == (self.start_x, 100_064)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 6)
        assert self.ship.coords == (self.start_x, 100_090)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 7)
        assert self.ship.coords == (self.start_x, 100_120)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 8)
        assert self.ship.coords == (self.start_x, 100_154)

    def test_ship_position_accelerate_from_0_velocity_e(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = 0
        self.ship.heading = constants.DEGREES_EAST
        self.ship.engine_lit = True

        # when ship is accelerating, delta velocity is linear and delta coords is exponential
        delta_velocity_per_frame = 0.8527131782945736

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 1)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_004, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 2)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_013, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 3)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_026, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 4)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_043, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 5)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_064, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 6)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_090, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 7)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_120, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 8)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_154, self.start_y)

    def test_ship_position_accelerate_from_0_velocity_s(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = 0
        self.ship.heading = constants.DEGREES_SOUTH
        self.ship.engine_lit = True

        # when ship is accelerating, delta velocity is linear and position change is exponential
        delta_velocity_per_frame = 0.8527131782945736

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -1)
        assert self.ship.coords == (self.start_x, 100_000 - 4)


        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -2)
        assert self.ship.coords == (self.start_x, 100_000 - 13)


        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -3)
        assert self.ship.coords == (self.start_x, 100_000 - 26)


        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -4)
        assert self.ship.coords == (self.start_x, 100_000 - 43)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -5)
        assert self.ship.coords == (self.start_x, 100_000 - 64)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -6)
        assert self.ship.coords == (self.start_x, 100_000 - 90)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -7)
        assert self.ship.coords == (self.start_x, 100_000 - 120)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -8)
        assert self.ship.coords == (self.start_x, 100_000 - 154)

    def test_ship_position_accelerate_from_0_velocity_w(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = 0
        self.ship.heading = constants.DEGREES_WEST
        self.ship.engine_lit = True

        # when ship is accelerating, delta velocity is linear and delta coords is exponential
        delta_velocity_per_frame = 0.8527131782945736

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -1)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_000 - 4, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -2)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_000 - 13, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -3)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_000 - 26, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -4)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_000 - 43, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -5)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_000 - 64, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -6)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_000 - 90, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -7)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_000 - 120, self.start_y)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -8)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_000 - 154, self.start_y)


    ''' ACCELERATE along cardinal headings (N/S/E/W) with retrograde heading.
    '''

    def test_ship_position_accelerate_s_with_n_velocity(self):
        delta_velocity_per_frame = 0.8527131782945736
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = delta_velocity_per_frame * 2
        self.ship.heading = constants.DEGREES_SOUTH
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 1)
        assert self.ship.coords == (100_000, 100_004)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 0)
        assert self.ship.coords == (100_000, 100_004)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -1)
        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -2)
        assert self.ship.coords == (100_000, 99_991)


    def test_ship_position_accelerate_n_with_s_velocity(self):
        delta_velocity_per_frame = 0.8527131782945736
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = delta_velocity_per_frame * -2
        self.ship.heading = constants.DEGREES_NORTH
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * -1)
        assert self.ship.coords == (100_000, 99_996)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 0)
        assert self.ship.coords == (100_000, 99_996)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 1)
        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, delta_velocity_per_frame * 2)
        assert self.ship.coords == (100_000, 100_009)


    def test_ship_position_accelerate_w_with_e_velocity(self):
        delta_velocity_per_frame = 0.8527131782945736
        self.ship.velocity_x_meters_per_second = delta_velocity_per_frame * 2
        self.ship.velocity_y_meters_per_second = 0
        self.ship.heading = constants.DEGREES_WEST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 1)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_004, 100_000)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_004, 100_000)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -1)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -2)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (99_991, 100_000)


    def test_ship_position_accelerate_e_with_w_velocity(self):
        delta_velocity_per_frame = 0.8527131782945736
        self.ship.velocity_x_meters_per_second = delta_velocity_per_frame * -2
        self.ship.velocity_y_meters_per_second = 0
        self.ship.heading = constants.DEGREES_EAST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * -1)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (99_996, 100_000)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (99_996, 100_000)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 1)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 2)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_009, 100_000)


    ''' ACCELERATE along inter-cardinal headings (NE/SE/SW/NW) with retrograde heading.
    '''

    def test_ship_position_accelerate_ne_with_sw_velocity(self):
        self.ship.velocity_x_meters_per_second = -5
        self.ship.velocity_y_meters_per_second = -5
        self.ship.heading = constants.DEGREES_NORTH_EAST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -4.3970)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -4.3970)
        assert self.ship.coords == (99_978, 99_978) # -22

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -3.7941)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -3.7941)
        assert self.ship.coords == (99_959, 99_959) # -19

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -3.1911)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -3.1911)
        assert self.ship.coords == (99_943, 99_943) # -16

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -2.5882)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -2.5882)
        assert self.ship.coords == (99_930, 99_930) # -13

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -1.9852)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -1.9852)
        assert self.ship.coords == (999_20, 999_20) # -10

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -1.3822)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -1.3822)
        assert self.ship.coords == (99_913, 99_913) # -7

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.7793)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -0.7793)
        assert self.ship.coords == (99_909, 99_909) # -4

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.1763)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -0.1763)
        assert self.ship.coords == (99_908, 99_908) # -1

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.4266)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.4266)
        assert self.ship.coords == (99_910, 99_910) # +2

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 1.0296)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 1.0296)
        assert self.ship.coords == (99_915, 99_915) # +5

    def test_ship_position_accelerate_se_with_nw_velocity(self):
        self.ship.velocity_x_meters_per_second = -5
        self.ship.velocity_y_meters_per_second = 5
        self.ship.heading = constants.DEGREES_SOUTH_EAST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()

        assert_floats_equal(self.ship.velocity_x_meters_per_second, -4.3970)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 4.3970)
        assert self.ship.coords == (99_978, 100022)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -3.7941)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.7941)
        assert self.ship.coords == (99_959, 100041)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -3.1911)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.1911)
        assert self.ship.coords == (99_943, 100_057)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -2.5882)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 2.5882)
        assert self.ship.coords == (99_930, 100_070)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -1.9852)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 1.9852)
        assert self.ship.coords == (999_20, 100_080)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -1.3822)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 1.3822)
        assert self.ship.coords == (99_913, 100_087)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.7793)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.7793)
        assert self.ship.coords == (99_909, 100_091)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.1763)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.1763)
        assert self.ship.coords == (99_908, 100_092)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.4266)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -0.4266)
        assert self.ship.coords == (99_910, 100_090)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 1.0296)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -1.0296)
        assert self.ship.coords == (99_915, 100_085)


    def test_ship_position_accelerate_sw_with_ne_velocity(self):
        self.ship.velocity_x_meters_per_second = 5
        self.ship.velocity_y_meters_per_second = 5
        self.ship.heading = constants.DEGREES_SOUTH_WEST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()

        assert_floats_equal(self.ship.velocity_x_meters_per_second, 4.3970)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 4.3970)
        assert self.ship.coords == (100022, 100022)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 3.7941)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.7941)
        assert self.ship.coords == (100041, 100041)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 3.1911)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.1911)
        assert self.ship.coords == (100_057, 100_057)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 2.5882)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 2.5882)
        assert self.ship.coords == (100_070, 100_070)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 1.9852)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 1.9852)
        assert self.ship.coords == (100_080, 100_080)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 1.3822)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 1.3822)
        assert self.ship.coords == (100_087, 100_087)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.7793)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.7793)
        assert self.ship.coords == (100_091, 100_091)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.1763)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.1763)
        assert self.ship.coords == (100_092, 100_092)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.4266)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -0.4266)
        assert self.ship.coords == (100_090, 100_090)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -1.0296)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -1.0296)
        assert self.ship.coords == (100_085, 100_085)


    def test_ship_position_accelerate_nw_with_se_velocity(self):
        self.ship.velocity_x_meters_per_second = 5
        self.ship.velocity_y_meters_per_second = -5
        self.ship.heading = constants.DEGREES_NORTH_WEST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 4.3970)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -4.3970)
        assert self.ship.coords == (100022, 99_978)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 3.7941)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -3.7941)
        assert self.ship.coords == (100041, 99_959)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 3.1911)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -3.1911)
        assert self.ship.coords == (100_057, 99_943)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 2.5882)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -2.5882)
        assert self.ship.coords == (100_070, 99_930)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 1.9852)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -1.9852)
        assert self.ship.coords == (100_080, 999_20)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 1.3822)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -1.3822)
        assert self.ship.coords == (100_087, 99_913)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.7793)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -0.7793)
        assert self.ship.coords == (100_091, 99_909)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.1763)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -0.1763)
        assert self.ship.coords == (100_092, 99_908)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.4266)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.4266)
        assert self.ship.coords == (100_090, 99_910)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -1.0296)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 1.0296)
        assert self.ship.coords == (100_085, 99_915)


    ''' ACCELERATE along cardinal headings (N/S/E/W) with +/- 90 degree perpendicular heading.
    '''

    def test_ship_position_accelerate_e_from_with_n_velocity(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = 5
        self.ship.heading = constants.DEGREES_EAST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.8527)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 5.0)
        assert self.ship.coords == (100_004, 100_025)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.8527 * 2)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 5.0)
        assert self.ship.coords == (100_012, 100_050)

    def test_ship_position_accelerate_w_from_with_n_velocity(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = 5
        self.ship.heading = constants.DEGREES_WEST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.8527)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 5.0)
        assert self.ship.coords == (99_996, 100_025)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.8527 * 2)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 5.0)
        assert self.ship.coords == (99_988, 100_050)

    def test_ship_position_accelerate_e_from_with_s_velocity(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = -5
        self.ship.heading = constants.DEGREES_EAST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.8527)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -5.0)
        assert self.ship.coords == (100_004, 99_975)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.8527 * 2)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -5.0)
        assert self.ship.coords == (100_012, 99_950)

    def test_ship_position_accelerate_w_from_with_s_velocity(self):
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = -5
        self.ship.heading = constants.DEGREES_WEST
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.8527)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -5.0)
        assert self.ship.coords == (99_996, 99_975)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.8527 * 2)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, -5.0)
        assert self.ship.coords == (99_988, 99_950)


    ''' ACCELERATE along headings that are normal/anti-normal with both x & y velocity.
    '''
    def test_ship_position_accelerate_ne_from_with_nw_velocity(self):
        """ Y velocity will steadily increase staying positive
            X velocity will steadily increase from negative to positive
            Ship position will go from origin, into quadrant 2, then into quadrant 1.
        """
        self.ship.velocity_x_meters_per_second = -2.0
        self.ship.velocity_y_meters_per_second = 3.5
        self.ship.heading = 63
        self.ship.engine_lit = True

        # Ship at origin
        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        # Ship in Quad 2
        assert_coord_in_quadrant(2, self.ship.coords)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -1.2402)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.8871)
        assert self.ship.coords == (99_994, 100_019)

        self._calculate_physics()
        assert_coord_in_quadrant(2, self.ship.coords)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -0.4805)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 4.2742)
        assert self.ship.coords == (99_992, 100_041)

        self._calculate_physics()
        assert_coord_in_quadrant(2, self.ship.coords)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0.2793)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 4.6614)
        assert self.ship.coords == (99_993, 100_064)

        self._calculate_physics()
        assert_coord_in_quadrant(2, self.ship.coords)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 1.0391)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 5.0485)
        assert self.ship.coords == (99_998, 100_089)

        self._calculate_physics()
        # Ship in Quad 1
        assert_coord_in_quadrant(1, self.ship.coords)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 1.7989)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 5.4356)
        assert self.ship.coords == (100_007, 100_117)


    def test_ship_position_accelerate_sw_from_with_nw_velocity(self):
        """ Y velocity will steadily decrease, going from positive to negative
            X velocity will steadily decrease, staying negative
            Ship position will go from origin, into quadrant 2, then into quadrant 3.
        """
        self.ship.velocity_x_meters_per_second = -2.0
        self.ship.velocity_y_meters_per_second = 3.5
        self.ship.heading = 255
        self.ship.engine_lit = True

        # Ship at origin
        assert self.ship.coords == TEST_ORIGIN

        self._calculate_physics()
        # Ship in Quad 2
        assert_coord_in_quadrant(2, self.ship.coords)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -2.8237)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.2793)
        assert self.ship.coords == (99_986, 100_017)

        self._calculate_physics()
        assert_coord_in_quadrant(2, self.ship.coords)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -3.6473)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.0586)
        assert self.ship.coords == (99_968, 100_032)

        self._calculate_physics()
        assert_coord_in_quadrant(2, self.ship.coords)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, -4.4710)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 2.8379)
        assert self.ship.coords == (99_946, 100_046)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 2, 3,
            x_velocity_profile=PROFILE_DECREASE,
            y_velocity_profile=PROFILE_DECREASE,
        )

    def test_ship_position_accelerate_nw_from_with_sw_velocity(self):
        """ Y velocity will steadily increase, going from negative to positive
            X velocity will steadily decrease, staying negative
            Ship position will go from origin, into quadrant 3, then into quadrant 2.
        """
        self.ship.velocity_x_meters_per_second = -2.0
        self.ship.velocity_y_meters_per_second = -3.5
        self.ship.heading = 342
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(3, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 3, 2,
            x_velocity_profile=PROFILE_DECREASE,
            y_velocity_profile=PROFILE_INCREASE,
        )

    def test_ship_position_accelerate_se_from_with_sw_velocity(self):
        """ Y velocity will steadily decrease, staying negative
            X velocity will steadily increase, going from negative to postive
            Ship position will go from origin, into quadrant 3, then into quadrant 4.
        """
        self.ship.velocity_x_meters_per_second = -2.0
        self.ship.velocity_y_meters_per_second = -3.5
        self.ship.heading = 116
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(3, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 3, 4,
            x_velocity_profile=PROFILE_INCREASE,
            y_velocity_profile=PROFILE_DECREASE,
        )

    def test_ship_position_accelerate_sw_from_with_se_velocity(self):
        """ Y velocity will steadily decrease, staying negative
            X velocity will steadily decrease, going from negative to positive
            Ship position will go from origin, into quadrant 4, then into quadrant 3.
        """
        self.ship.velocity_x_meters_per_second = 2.0
        self.ship.velocity_y_meters_per_second = -3.5
        self.ship.heading = 223
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(4, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 4, 3,
            x_velocity_profile=PROFILE_DECREASE,
            y_velocity_profile=PROFILE_DECREASE,
        )

    def test_ship_position_accelerate_ne_from_with_se_velocity(self):
        """ Y velocity will steadily increase, going from negative to positive
            X velocity will steadily increase, staying positive
            Ship position will go from origin, into quadrant 4, then into quadrant 1.
        """
        self.ship.velocity_x_meters_per_second = 2.0
        self.ship.velocity_y_meters_per_second = -3.5
        self.ship.heading = 50
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(4, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 4, 1,
            x_velocity_profile=PROFILE_INCREASE,
            y_velocity_profile=PROFILE_INCREASE,
        )

    def test_ship_position_accelerate_nw_from_with_ne_velocity(self):
        """ Y velocity will steadily increase, staying positive
            X velocity will steadily decrease, going from positive to negative
            Ship position will go from origin, into quadrant 1, then into quadrant 2.
        """
        self.ship.velocity_x_meters_per_second = 2.0
        self.ship.velocity_y_meters_per_second = 3.5
        self.ship.heading = 330
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(1, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 1, 2,
            x_velocity_profile=PROFILE_DECREASE,
            y_velocity_profile=PROFILE_INCREASE,
        )

    def test_ship_position_accelerate_se_from_with_ne_velocity(self):
        """ Y velocity will steadily decrease, going from positive to negative
            X velocity will steadily increase, staying positive
            Ship position will go from origin, into quadrant 1, then into quadrant 4.
        """
        self.ship.velocity_x_meters_per_second = 2.0
        self.ship.velocity_y_meters_per_second = 3.5
        self.ship.heading = 98
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(1, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 1, 4,
            x_velocity_profile=PROFILE_INCREASE,
            y_velocity_profile=PROFILE_DECREASE,
        )

    def test_ship_position_accelerate_nw_from_with_se_velocity_into_quad_3(self):
        """ Y velocity will steadily increase, going from negative to positive
            X velocity will steadily decrease, going from positive to negative
            Ship position will go from origin, into quadrant 4, then into quadrant 3
                (and eventually to quad 2).
        """

        self.ship.velocity_x_meters_per_second = 2.0
        self.ship.velocity_y_meters_per_second = -3.5
        self.ship.heading = 280
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(4, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 4, 3,
            x_velocity_profile=PROFILE_DECREASE,
            y_velocity_profile=PROFILE_INCREASE,
        )

    def test_ship_position_accelerate_nw_from_with_se_velocity_into_quad_1(self):
        """ Y velocity will steadily increase, going from negative to positive
            X velocity will steadily decrease, going from positive to negative
            Ship position will go from origin, into quadrant 4, then into quadrant 1
                (and eventually to quad 2).
        """

        self.ship.velocity_x_meters_per_second = 3.0
        self.ship.velocity_y_meters_per_second = -2
        self.ship.heading = 330
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(4, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 4, 1,
            x_velocity_profile=PROFILE_DECREASE,
            y_velocity_profile=PROFILE_INCREASE,
        )



    def test_ship_position_accelerate_sw_from_with_ne_velocity_into_quad_2(self):
        """ Y velocity will steadily decrease, going from positive to negative
            X velocity will steadily decrease, going from positive to negative
            Ship position will go from origin, into quadrant 1, then into quadrant 2
                (and eventually to quad 3).
        """

        self.ship.velocity_x_meters_per_second = 2.0
        self.ship.velocity_y_meters_per_second = 3.5
        self.ship.heading = 255
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(1, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 1, 2,
            x_velocity_profile=PROFILE_DECREASE,
            y_velocity_profile=PROFILE_DECREASE,
        )

    def test_ship_position_accelerate_sw_from_with_ne_velocity_into_quad_4(self):
        """ Y velocity will steadily decrease, going from positive to negative
            X velocity will steadily decrease, going from positive to negative
            Ship position will go from origin, into quadrant 1, then into quadrant 2
                (and eventually to quad 3).
        """

        self.ship.velocity_x_meters_per_second = 3.5
        self.ship.velocity_y_meters_per_second = 2
        self.ship.heading = 195
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(1, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 1, 4,
            x_velocity_profile=PROFILE_DECREASE,
            y_velocity_profile=PROFILE_DECREASE,
        )

    def test_ship_position_accelerate_ne_from_with_sw_velocity_into_quad_2(self):
        """ Y velocity will steadily increase, going from negative to positive
            X velocity will steadily increase, going from negative to positive
            Ship position will go from origin, into quadrant 3, then into quadrant 2
                (and eventually to quad 1).
        """
        self.ship.velocity_x_meters_per_second = -2.5
        self.ship.velocity_y_meters_per_second = -3.5
        self.ship.heading = 25
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(3, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 3, 2,
            x_velocity_profile=PROFILE_INCREASE,
            y_velocity_profile=PROFILE_INCREASE,
        )

    def test_ship_position_accelerate_ne_from_with_sw_velocity_into_quad_4(self):
        """ Y velocity will steadily increase, going from negative to positive
            X velocity will steadily increase, going from negative to positive
            Ship position will go from origin, into quadrant 3, then into quadrant 2
                (and eventually to quad 1).
        """
        self.ship.velocity_x_meters_per_second = -3.5
        self.ship.velocity_y_meters_per_second = -2.5
        self.ship.heading = 80
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(3, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 3, 4,
            x_velocity_profile=PROFILE_INCREASE,
            y_velocity_profile=PROFILE_INCREASE,
        )

    def test_ship_position_accelerate_se_from_with_nw_velocity_into_quad_1(self):
        """ Y velocity will steadily decrease, going from positive to negative
            X velocity will steadily increase, going from negative to positive
            Ship position will go from origin, into quadrant 2, then into quadrant 1
                (and eventually to quad 4).
        """
        self.ship.velocity_x_meters_per_second = -2.5
        self.ship.velocity_y_meters_per_second = 3.5
        self.ship.heading = 95
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(2, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 2, 1,
            x_velocity_profile=PROFILE_INCREASE,
            y_velocity_profile=PROFILE_DECREASE,
        )

    def test_ship_position_accelerate_se_from_with_nw_velocity_into_quad_3(self):
        """ Y velocity will steadily decrease, going from positive to negative
            X velocity will steadily increase, going from negative to positive
            Ship position will go from origin, into quadrant 2, then into quadrant 3
                (and eventually to quad 4).
        """
        self.ship.velocity_x_meters_per_second = -3.5
        self.ship.velocity_y_meters_per_second = 2.5
        self.ship.heading = 150
        self.ship.engine_lit = True

        assert self.ship.coords == TEST_ORIGIN
        self._calculate_physics()
        assert_coord_in_quadrant(2, self.ship.coords)
        assert_ship_moves_from_quadrant_to_quadrant(
            self.ship, self.fps, 2, 3,
            x_velocity_profile=PROFILE_INCREASE,
            y_velocity_profile=PROFILE_DECREASE,
        )



'''
███████ ███████ ████████     ██   ██ ███████  █████  ██████  ██ ███    ██  ██████
██      ██         ██        ██   ██ ██      ██   ██ ██   ██ ██ ████   ██ ██
███████ █████      ██        ███████ █████   ███████ ██   ██ ██ ██ ██  ██ ██   ███
     ██ ██         ██        ██   ██ ██      ██   ██ ██   ██ ██ ██  ██ ██ ██    ██
███████ ███████    ██        ██   ██ ███████ ██   ██ ██████  ██ ██   ████  ██████
'''

class TestShipCMDSetHeading(TestCase):

    def setUp(self):
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=10)
        self.ship.reaction_wheel_online = True

    def _assert_ship_heading_0(self):
        assert self.ship.heading == constants.DEGREES_NORTH
        assert self.ship.rel_rot_coord_0 == (-20, -60)
        assert self.ship.rel_rot_coord_1 == (-20, 60)
        assert self.ship.rel_rot_coord_2 == (20, 60)
        assert self.ship.rel_rot_coord_3 == (20, -60)
        assert self.ship.rel_rot_coord_0 == self.ship.heading_0_rel_coord_0
        assert self.ship.rel_rot_coord_1 == self.ship.heading_0_rel_coord_1
        assert self.ship.rel_rot_coord_2 == self.ship.heading_0_rel_coord_2
        assert self.ship.rel_rot_coord_3 == self.ship.heading_0_rel_coord_3

    def _assert_heading_0_cords_fixed(self):
        assert self.ship.heading_0_rel_coord_0 == (-20, -60)
        assert self.ship.heading_0_rel_coord_1 == (-20, 60)
        assert self.ship.heading_0_rel_coord_2 == (20, 60)
        assert self.ship.heading_0_rel_coord_3 == (20, -60)

    def test_ship_cannot_rotate_if_reaction_wheel_is_offline(self):
        self._assert_ship_heading_0()
        self.ship.reaction_wheel_online = False
        self.ship.cmd_set_heading(30)
        self._assert_ship_heading_0()

    def test_rotate_ship_to_0_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(constants.DEGREES_NORTH)
        self._assert_ship_heading_0()
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_90_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(constants.DEGREES_EAST)
        assert self.ship.heading == constants.DEGREES_EAST
        assert self.ship.rel_rot_coord_0 == (-60, 20,)
        assert self.ship.rel_rot_coord_1 == (60, 20,)
        assert self.ship.rel_rot_coord_2 ==  (60, -20,)
        assert self.ship.rel_rot_coord_3 == (-60, -20,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_180_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(constants.DEGREES_SOUTH)
        assert self.ship.heading == constants.DEGREES_SOUTH
        assert self.ship.rel_rot_coord_0 == (20, 60,)
        assert self.ship.rel_rot_coord_1 == (20, -60,)
        assert self.ship.rel_rot_coord_2 ==  (-20, -60,)
        assert self.ship.rel_rot_coord_3 == (-20, 60,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_270_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(constants.DEGREES_WEST)
        assert self.ship.heading == constants.DEGREES_WEST
        assert self.ship.rel_rot_coord_0 == (60, -20,)
        assert self.ship.rel_rot_coord_1 == (-60, -20,)
        assert self.ship.rel_rot_coord_2 ==  (-60, 20,)
        assert self.ship.rel_rot_coord_3 == (60, 20,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_quad_1_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(30)
        assert self.ship.heading == 30
        assert self.ship.rel_rot_coord_0 == (-47, -42,)
        assert self.ship.rel_rot_coord_1 == (13, 62,)
        assert self.ship.rel_rot_coord_2 ==  (47, 42,)
        assert self.ship.rel_rot_coord_3 == (-13, -62,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_quad_2_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(139)
        assert self.ship.heading == 139
        assert self.ship.rel_rot_coord_0 == (-24, 58,)
        assert self.ship.rel_rot_coord_1 == (54, -32,)
        assert self.ship.rel_rot_coord_2 == (24, -58,)
        assert self.ship.rel_rot_coord_3 == (-54, 32,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_quad_3_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(226)
        assert self.ship.heading == 226
        assert self.ship.rel_rot_coord_0 == (57, 27,)
        assert self.ship.rel_rot_coord_1 == (-29, -56,)
        assert self.ship.rel_rot_coord_2 == (-57, -27,)
        assert self.ship.rel_rot_coord_3 == (29, 56,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_quad_4_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(305)
        assert self.ship.heading == 305
        assert self.ship.rel_rot_coord_0 == (38, -51,)
        assert self.ship.rel_rot_coord_1 == (-61, 18,)
        assert self.ship.rel_rot_coord_2 == (-38, 51,)
        assert self.ship.rel_rot_coord_3 == (61, -18,)
        self._assert_heading_0_cords_fixed()


'''
██████  ███████  █████   ██████ ████████ ██  ██████  ███    ██
██   ██ ██      ██   ██ ██         ██    ██ ██    ██ ████   ██
██████  █████   ███████ ██         ██    ██ ██    ██ ██ ██  ██
██   ██ ██      ██   ██ ██         ██    ██ ██    ██ ██  ██ ██
██   ██ ███████ ██   ██  ██████    ██    ██  ██████  ██   ████

██     ██ ██   ██ ███████ ███████ ██
██     ██ ██   ██ ██      ██      ██
██  █  ██ ███████ █████   █████   ██
██ ███ ██ ██   ██ ██      ██      ██
 ███ ███  ██   ██ ███████ ███████ ███████
'''


class TestShipCMDActivateAndDeactivateReactionWheel(TestCase):

    def setUp(self):
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=10)
        self.ship.reaction_wheel_online = False

    def test_reaction_wheel_can_be_activated(self):
        assert not self.ship.reaction_wheel_online
        start_power = self.ship.battery_power
        self.ship.cmd_set_reaction_wheel_status(True)

        assert self.ship.reaction_wheel_online
        assert (
            self.ship.battery_power
            == (start_power - constants.ACTIVATE_REACTION_WHEEL_POWER_REQUIREMENT)
        )

    def test_reaction_wheel_cant_be_activated_if_not_enough_power(self):
        assert not self.ship.reaction_wheel_online
        self.ship.battery_power = constants.ACTIVATE_REACTION_WHEEL_POWER_REQUIREMENT // 2
        start_power = self.ship.battery_power
        self.ship.cmd_set_reaction_wheel_status(True)

        assert not self.ship.reaction_wheel_online
        assert self.ship.battery_power == start_power

    def test_reaction_wheel_can_be_shut_off(self):
        self.ship.reaction_wheel_online = True
        self.ship.cmd_set_reaction_wheel_status(False)
        assert not self.ship.reaction_wheel_online


'''
███████ ███    ██  ██████  ██ ███    ██ ███████
██      ████   ██ ██       ██ ████   ██ ██
█████   ██ ██  ██ ██   ███ ██ ██ ██  ██ █████
██      ██  ██ ██ ██    ██ ██ ██  ██ ██ ██
███████ ██   ████  ██████  ██ ██   ████ ███████
'''

class TestShipCMDActivateDeactivateLightEngine(TestCase):
    def setUp(self):
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=10)

    def test_activate_engine_command_updates_ship_state(self):
        current_frame = 10
        assert self.ship._state == {}
        self.ship.game_frame = current_frame
        self.ship.cmd_activate_engine()
        assert self.ship.engine_starting
        assert self.ship.engine_start_complete_at_frame == current_frame + self.ship.engine_frames_to_activate

    def test_deactivate_engine_command_updates_ship_state(self):
        self.ship.engine_online = True
        self.ship.engine_lit = True
        self.ship.cmd_deactivate_engine()
        assert not self.ship.engine_online
        assert not self.ship.engine_lit

    def test_ship_engine_can_be_lit(self):
        self.ship.engine_online = True
        self.ship.engine_lit = False
        assert not self.ship.engine_lit
        self.ship.cmd_light_engine()
        assert self.ship.engine_lit
        assert self.ship.engine_online
