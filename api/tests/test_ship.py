
from unittest import TestCase

from api.models.ship import ShipStateKey
from api import constants
from .utils import (
    DebugShip as Ship,
    assert_floats_equal,
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
        self.ship = Ship.spawn(map_units_per_meter=10)
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
        self.ship._state[ShipStateKey.ENGINE] = {
            'starting': True,
            'last_frame': 3,
        }
        start_battery_power = self.ship.battery_power
        power_usage_per_frame_eng_start = self.ship.engine_activation_power_required_per_frame

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 1
        assert not self.ship.engine_online
        assert ShipStateKey.ENGINE in self.ship._state

        self.ship.game_frame = 2
        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 2
        assert not self.ship.engine_online
        assert ShipStateKey.ENGINE in self.ship._state

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
        assert ShipStateKey.ENGINE not in self.ship._state

    def test_engine_start_process_fails_if_not_enough_power(self):
        ''' ENGINE ACTIVATE '''
        self.ship.game_frame = 1
        self.ship._state[ShipStateKey.ENGINE] = {
            'starting': True,
            'last_frame': 3,
        }
        start_battery_power = self.ship.battery_power
        power_usage_per_frame_eng_start = self.ship.engine_activation_power_required_per_frame

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 1
        assert not self.ship.engine_online
        assert ShipStateKey.ENGINE in self.ship._state

        self.ship.game_frame = 2
        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 2
        assert not self.ship.engine_online
        assert ShipStateKey.ENGINE in self.ship._state

        self.ship.game_frame = 3
        self.ship.battery_power = 0
        self.ship.adjust_resources()
        assert not self.ship.engine_online
        assert not self.ship.engine_lit
        assert ShipStateKey.ENGINE not in self.ship._state

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
        self.ship = Ship.spawn(map_units_per_meter=self.map_units_per_meter)

        # Set values that are used in physics calculations.
        self.ship.engine_newtons = 1100
        self.ship._state[ShipStateKey.MASS] = 645
        self.fps = 2
        self._reset_ship()

    def _reset_ship(self):
        self.ship.coord_x = 100_000
        self.ship.coord_y = 100_000
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


    def test_ship_position_accelerate_s_with_n_velocity(self):
        delta_velocity_per_frame = 0.8527131782945736
        self.ship.velocity_x_meters_per_second = 0
        self.ship.velocity_y_meters_per_second = delta_velocity_per_frame * 2
        self.ship.heading = constants.DEGREES_SOUTH
        self.ship.engine_lit = True

        assert self.ship.coords == (100_000, 100_000)

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
        assert self.ship.coords == (100_000, 100_000)

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

        assert self.ship.coords == (100_000, 100_000)

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
        assert self.ship.coords == (100_000, 100_000)

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

        assert self.ship.coords == (100_000, 100_000)

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
        assert self.ship.coords == (100_000, 100_000)

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

        assert self.ship.coords == (100_000, 100_000)

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
        assert self.ship.coords == (100_000, 100_000)

        self._calculate_physics()
        assert_floats_equal(self.ship.velocity_x_meters_per_second, delta_velocity_per_frame * 2)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0.0)
        assert self.ship.coords == (100_009, 100_000)


    def test_ship_position_accelerate_ne_with_sw_velocity(self):
        delta_velocity_per_frame = 0.8527131782945736
        self.ship.velocity_x_meters_per_second = -5
        self.ship.velocity_y_meters_per_second = -5
        self.ship.heading = constants.DEGREES_NORTH_EAST
        self.ship.engine_lit = True

        assert self.ship.coords == (100_000, 100_000)

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


'''
███████ ███████ ████████     ██   ██ ███████  █████  ██████  ██ ███    ██  ██████
██      ██         ██        ██   ██ ██      ██   ██ ██   ██ ██ ████   ██ ██
███████ █████      ██        ███████ █████   ███████ ██   ██ ██ ██ ██  ██ ██   ███
     ██ ██         ██        ██   ██ ██      ██   ██ ██   ██ ██ ██  ██ ██ ██    ██
███████ ███████    ██        ██   ██ ███████ ██   ██ ██████  ██ ██   ████  ██████
'''

class TestShipCMDSetHeading(TestCase):

    def setUp(self):
        self.ship = Ship.spawn(map_units_per_meter=10)
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
        self.ship = Ship.spawn(map_units_per_meter=10)
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
        self.ship = Ship.spawn(map_units_per_meter=10)

    def test_activate_engine_command_updates_ship_state(self):
        current_frame = 10
        assert self.ship._state == {}
        self.ship.game_frame = current_frame
        self.ship.cmd_activate_engine()
        assert self.ship._state == {
            ShipStateKey.ENGINE: {
                'starting': True,
                'last_frame': current_frame + self.ship.engine_frames_to_activate,
            }
        }

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
