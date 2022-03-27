
from unittest import TestCase
from uuid import uuid4

from api.models.ship import AutoPilotPrograms, ShipStateKey
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



class TestShipBasicMethods(TestCase):
    def setUp(self):
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=10)

    def test_to_dict_method_returns_a_dict(self):
        assert isinstance(self.ship.to_dict(), dict)



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

    def test_engine_start_process_uses_power(self):
        ''' ENGINE ACTIVATE '''
        self.ship.engine_starting = True
        self.ship.battery_power = 5000
        self.ship.engine_activation_power_required_total = 3000
        self.ship.engine_activation_power_required_per_second = 2000
        self.ship.engine_idle_power_requirement_per_second = 100
        self.ship.engine_startup_power_used = 0
        start_power = self.ship.battery_power

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == start_power - 1000
        assert self.ship.engine_startup_power_used == 1000
        assert self.ship.engine_starting
        assert not self.ship.engine_online
        assert not self.ship.engine_lit

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == start_power - 2000
        assert self.ship.engine_startup_power_used == 2000
        assert self.ship.engine_starting
        assert not self.ship.engine_online
        assert not self.ship.engine_lit

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == start_power - 3000
        assert self.ship.engine_startup_power_used == 3000
        assert self.ship.engine_starting
        assert not self.ship.engine_online
        assert not self.ship.engine_lit

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == start_power - (3000 + 50)
        assert self.ship.engine_startup_power_used is None
        assert self.ship.engine_online
        assert not self.ship.engine_lit
        assert not self.ship.engine_starting

    def test_engine_start_process_fails_if_not_enough_power(self):
        ''' ENGINE ACTIVATE '''
        self.ship.engine_starting = True
        self.ship.battery_power = 2500
        self.ship.engine_activation_power_required_total = 3000
        self.ship.engine_activation_power_required_per_second = 2000
        self.ship.engine_idle_power_requirement_per_second = 100
        self.ship.engine_startup_power_used = 0
        start_power = self.ship.battery_power

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == start_power - 1000
        assert self.ship.engine_startup_power_used == 1000
        assert not self.ship.engine_online
        assert self.ship.engine_starting

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == start_power - 2000
        assert self.ship.engine_startup_power_used == 2000
        assert not self.ship.engine_online
        assert self.ship.engine_starting

        # Startup cancelled.
        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == start_power - 2000
        assert self.ship.engine_startup_power_used is None
        assert not self.ship.engine_online
        assert not self.ship.engine_starting

    def test_idle_engine_uses_power(self):
        ''' ENGINE IDLE '''
        self.ship.engine_online = True
        self.ship.battery_power = 2500
        self.ship.fuel_level = 10000
        self.ship.engine_idle_power_requirement_per_second = 100
        starting_fuel = self.ship.fuel_level
        starting_power = self.ship.battery_power

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == starting_power - 50
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == starting_power - 100
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

    def test_idle_engine_deactivates_if_not_enough_power(self):
        ''' ENGINE IDLE '''
        self.ship.engine_online = True
        self.ship.battery_power = 200
        self.ship.fuel_level = 10000
        self.ship.engine_idle_power_requirement_per_second = 100
        starting_fuel = self.ship.fuel_level
        starting_power = self.ship.battery_power

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == starting_power - 50
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == starting_power - 100
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == starting_power - 150
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == 0
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

        # Not enough power to idle the engine for another frame
        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.battery_power == 0
        assert self.ship.fuel_level == starting_fuel
        assert not self.ship.engine_online

    def test_lit_engine_uses_fuel_and_generates_power(self):
        ''' ENGINE LIT '''
        self.ship.engine_online = True
        self.ship.engine_lit = True
        self.ship.fuel_level = 10000
        self.ship.engine_fuel_usage_per_second = 100
        self.ship.engine_battery_charge_per_second = 500
        self.ship.battery_power = 10_000
        self.ship.battery_capacity = 100_000
        start_fuel = self.ship.fuel_level
        start_power = self.ship.battery_power

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.fuel_level == start_fuel - 50
        assert self.ship.battery_power == start_power + 250
        assert self.ship.engine_online
        assert self.ship.engine_lit

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.fuel_level == start_fuel - 100
        assert self.ship.battery_power == start_power + 500
        assert self.ship.engine_online
        assert self.ship.engine_lit

    def test_boosting_engine_uses_extra_fuel_and_is_boosted(self):
        ''' ENGINE BOOSTED '''
        self.ship.engine_online = True
        self.ship.engine_lit = True
        self.ship.engine_boosted = False
        self.ship.engine_boosting = True
        self.ship.engine_boost_multiple = 50
        self.ship.fuel_level = 100_000
        self.ship.engine_fuel_usage_per_second = 100
        self.ship.engine_battery_charge_per_second = 500
        self.ship.battery_power = 10_000
        self.ship.battery_capacity = 100_000

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.engine_boosting is False
        assert self.ship.engine_boosted is True
        expected_fuel = 100_000 - (50 + 50 * self.ship.engine_boost_multiple)
        assert self.ship.fuel_level == expected_fuel

    def test_boosting_engine_can_flame_out_the_engine(self):
        self.ship.engine_online = True
        self.ship.engine_lit = True
        self.ship.engine_boosted = False
        self.ship.engine_boosting = True
        self.ship.engine_boost_multiple = 50
        self.ship.fuel_level = 200
        self.ship.engine_fuel_usage_per_second = 100 # 50 fuel will get burned for let engine, then flame out due to boost
        self.ship.engine_battery_charge_per_second = 500
        self.ship.battery_power = 10_000
        self.ship.battery_capacity = 100_000

        self.ship.adjust_resources(fps=2, game_frame=1)
        # Flameout.
        assert self.ship.engine_boosting is False
        assert self.ship.engine_boosted is False
        assert self.ship.engine_lit is False
        assert self.ship.engine_online is False
        assert self.ship.fuel_level == 150

    def test_lit_engine_flames_out_if_not_enough_fuel(self):
        ''' ENGINE LIT '''
        self.ship.engine_online = True
        self.ship.engine_lit = True
        self.ship.fuel_level = 100
        self.ship.engine_fuel_usage_per_second = 100
        self.ship.engine_battery_charge_per_second = 500
        self.ship.battery_power = 10_000
        self.ship.battery_capacity = 100_000
        start_power = self.ship.battery_power

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.fuel_level == 50
        assert self.ship.battery_power == start_power + 250
        assert self.ship.engine_online
        assert self.ship.engine_lit

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.fuel_level == 0
        assert self.ship.battery_power == start_power + 500
        assert self.ship.engine_online
        assert self.ship.engine_lit

        # Engine flame out.
        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.fuel_level == 0
        assert self.ship.battery_power == start_power + 500
        assert not self.ship.engine_online
        assert not self.ship.engine_lit

    def test_apu_start_process_uses_power(self):
        self.ship.apu_starting = True
        self.ship.apu_online = False
        self.ship.apu_startup_power_used = 0
        self.ship.fuel_level = 10_000
        self.ship.battery_power = 200_000
        self.ship.apu_activation_power_required_total = 500
        self.ship.apu_activation_power_required_per_second = 100

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.apu_starting
        assert not self.ship.apu_online
        assert self.ship.apu_startup_power_used == 50 * 1
        assert self.ship.battery_power == (200_000 - 50 * 1)
        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.apu_starting
        assert not self.ship.apu_online
        assert self.ship.apu_startup_power_used == 50 * 2
        assert self.ship.battery_power == (200_000 - 50 * 2)

    def test_apu_start_process_completes_and_the_apu_starts(self):
        self.ship.apu_starting = True
        self.ship.apu_online = False
        self.ship.apu_startup_power_used = 0
        self.ship.fuel_level = 10_000
        self.ship.battery_power = 200_000
        self.ship.apu_activation_power_required_total = 300
        self.ship.apu_activation_power_required_per_second = 100

        self.ship.adjust_resources(fps=1, game_frame=1)
        assert self.ship.apu_startup_power_used == 100
        assert self.ship.apu_starting
        assert not self.ship.apu_online
        self.ship.adjust_resources(fps=1, game_frame=1)
        assert self.ship.apu_startup_power_used == 200
        assert self.ship.apu_starting
        assert not self.ship.apu_online
        self.ship.adjust_resources(fps=1, game_frame=1)
        assert self.ship.apu_startup_power_used == 300
        assert self.ship.apu_starting
        assert not self.ship.apu_online
        assert self.ship.battery_power == 200_000 - 300
        self.ship.adjust_resources(fps=1, game_frame=1)
        assert not self.ship.apu_starting
        assert self.ship.apu_online

    def test_apu_start_is_interrupted_if_ship_runs_out_of_electricity(self):
        self.ship.apu_starting = True
        self.ship.apu_online = False
        self.ship.apu_startup_power_used = 0
        self.ship.fuel_level = 10_000
        self.ship.battery_power = 250
        self.ship.apu_activation_power_required_total = 300
        self.ship.apu_activation_power_required_per_second = 100

        self.ship.adjust_resources(fps=1, game_frame=1)
        assert self.ship.apu_startup_power_used == 100
        assert self.ship.apu_starting
        assert not self.ship.apu_online
        self.ship.adjust_resources(fps=1, game_frame=1)
        assert self.ship.apu_startup_power_used == 200
        assert self.ship.apu_starting
        assert not self.ship.apu_online
        # startup dies here
        self.ship.adjust_resources(fps=1, game_frame=1)
        assert not self.ship.apu_starting
        assert not self.ship.apu_online
        assert self.ship.battery_power == 50


    def test_online_apu_uses_fuel_and_generates_electricity(self):
        self.ship.apu_starting = False
        self.ship.apu_online = True
        self.ship.fuel_level = 10_000
        self.ship.battery_power = 200_000
        self.ship.apu_fuel_usage_per_second = 125
        self.ship.apu_battery_charge_per_second = 200

        self.ship.adjust_resources(fps=1, game_frame=1)
        assert self.ship.apu_online
        assert self.ship.fuel_level == 10_000 - 125
        assert self.ship.battery_power == 200_000 + 200

    def test_online_apu_shuts_down_if_ship_runs_out_of_fuel(self):
        self.ship.apu_starting = False
        self.ship.apu_online = True
        self.ship.fuel_level = 900
        self.ship.battery_power = 200_000
        self.ship.apu_fuel_usage_per_second = 1000
        self.ship.apu_battery_charge_per_second = 200

        self.ship.adjust_resources(fps=3, game_frame=1)
        assert self.ship.apu_online
        self.ship.adjust_resources(fps=3, game_frame=1)
        assert self.ship.apu_online
        # Flame out
        self.ship.adjust_resources(fps=3, game_frame=1)
        assert not self.ship.apu_online
        assert self.ship.fuel_level < 900


    def test_scanner_start_process_uses_power(self):
        ''' SCANNER ACTIVATE '''
        start_power = self.ship.battery_power
        self.ship.scanner_startup_power_used = 0
        self.ship.scanner_online = False
        self.ship.scanner_starting = True
        self.ship.scanner_activation_power_required_total = 1000
        self.ship.scanner_activation_power_required_per_second = 500
        self.ship.scanner_idle_power_requirement_per_second = 100

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - 250
        assert self.ship.scanner_startup_power_used == 250

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - 500
        assert self.ship.scanner_startup_power_used == 500

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - 750
        assert self.ship.scanner_startup_power_used == 750

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - 1000
        assert self.ship.scanner_startup_power_used == 1000

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert not self.ship.scanner_starting
        assert self.ship.scanner_online
        assert self.ship.battery_power == start_power - (1000 + 50) # 50 is the idle power used for the first frame of being online.
        assert self.ship.scanner_startup_power_used is None

        # Scanner is idling
        self.ship.adjust_resources(fps=2, game_frame=1)
        assert not self.ship.scanner_starting
        assert self.ship.scanner_online
        assert self.ship.battery_power == start_power - (1000 + 50 + 50)

    def test_scanner_start_process_fails_if_not_enough_power(self):
        ''' SCANNER ACTIVATE '''
        self.ship.scanner_online = False
        self.ship.scanner_starting = True
        self.ship.scanner_startup_power_used = 0
        self.ship.battery_power = 1000
        self.ship.scanner_activation_power_required_total = 2000
        self.ship.scanner_activation_power_required_per_second = 500
        self.ship.scanner_idle_power_requirement_per_second = 100
        start_power = self.ship.battery_power

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - 250
        assert self.ship.scanner_startup_power_used == 250

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - 500
        assert self.ship.scanner_startup_power_used == 500

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == start_power - 750
        assert self.ship.scanner_startup_power_used == 750

        self.ship.adjust_resources(fps=2, game_frame=1)
        assert self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == 0
        assert self.ship.scanner_startup_power_used == 1000

        # Startup cancelled.
        self.ship.adjust_resources(fps=2, game_frame=1)
        assert not self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == 0
        assert self.ship.scanner_startup_power_used is None

    def test_idle_scanner_uses_power(self):
        ''' SCANNER IDLE '''
        self.ship.scanner_online = True
        self.ship.battery_power = 1000
        self.ship.scanner_activation_power_required_per_second = 500
        self.ship.scanner_idle_power_requirement_per_second = 100
        fps = 2
        adj_per_frame = self.ship.scanner_idle_power_requirement_per_second / fps
        start_power = self.ship.battery_power

        for i in range(10):
            self.ship.adjust_resources(fps=fps, game_frame=1)
            assert not self.ship.scanner_starting
            assert self.ship.scanner_online
            assert self.ship.battery_power == start_power - (adj_per_frame * (i  + 1))

    def test_idle_scanner_deactivates_if_not_enough_power(self):
        ''' SCANNER IDLE '''
        self.ship.scanner_online = True
        self.ship.battery_power = 1000
        self.ship.scanner_idle_power_requirement_per_second = 1000
        fps = 2

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert not self.ship.scanner_starting
        assert self.ship.scanner_online
        assert self.ship.battery_power == 500

        # Scanner will function this frame, but will drain last of battery power
        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert not self.ship.scanner_starting
        assert self.ship.scanner_online
        assert self.ship.battery_power == 0

        # Scanner is deactivated this frame.
        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert not self.ship.scanner_starting
        assert not self.ship.scanner_online
        assert self.ship.battery_power == 0


    def test_ship_channeling_scanner_lock_uses_power(self):
        ''' SCANNER LOCKING '''
        self.ship.scanner_online = True
        self.ship.battery_power = 100_000
        self.ship.scanner_idle_power_requirement_per_second = 1000
        self.ship.scanner_get_lock_power_requirement_total = 1800
        self.ship.scanner_get_lock_power_requirement_per_second = 1000
        self.ship.scanner_locking = True
        self.ship.scanner_locking_power_used = 0
        self.ship.scanner_lock_target = "foobar"
        fps = 2

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 99_000
        assert self.ship.scanner_locking
        assert self.ship.scanner_locking_power_used == 500

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 98_000
        assert self.ship.scanner_locking
        assert self.ship.scanner_locking_power_used == 1000

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 97_000
        assert self.ship.scanner_locking
        assert self.ship.scanner_locking_power_used == 1500

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 96_200
        assert self.ship.scanner_locking
        assert self.ship.scanner_locking_power_used == 1800

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 95_700
        assert self.ship.scanner_locked
        assert not self.ship.scanner_locking
        assert self.ship.scanner_locking_power_used is None
        assert self.ship.scanner_lock_target == "foobar"


    def test_ship_channeling_scanner_lock_is_interrupted_if_not_enough_power(self):
        ''' SCANNER LOCKING '''
        self.ship.scanner_online = True
        self.ship.battery_power = 2500
        self.ship.scanner_idle_power_requirement_per_second = 1000
        self.ship.scanner_get_lock_power_requirement_total = 2000
        self.ship.scanner_get_lock_power_requirement_per_second = 1000
        self.ship.scanner_locking = True
        self.ship.scanner_locking_power_used = 0
        self.ship.scanner_lock_target = "foobar"
        fps = 2

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 1500
        assert self.ship.scanner_locking
        assert self.ship.scanner_locking_power_used == 500

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 500
        assert self.ship.scanner_locking
        assert self.ship.scanner_locking_power_used == 1000

        # Enough power to idle scanner (first draw) but lock channeling is cancelled
        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 0
        assert not self.ship.scanner_locking
        assert self.ship.scanner_locking_power_used is None
        assert self.ship.scanner_lock_target is None

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert not self.ship.scanner_online


    def test_ship_lock_is_lost_if_not_enough_power(self):
        ''' SCANNER LOCK '''
        self.ship.scanner_online = True
        self.ship.battery_power = 1500
        self.ship.scanner_idle_power_requirement_per_second = 1000
        self.ship.scanner_get_lock_power_requirement_total = 2000
        self.ship.scanner_get_lock_power_requirement_per_second = 1000
        self.ship.scanner_locking = False
        self.ship.scanner_locked = True
        self.ship.scanner_locking_power_used = None
        self.ship.scanner_lock_target = "foobar"
        fps = 2

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 1000
        assert not self.ship.scanner_locking
        assert self.ship.scanner_locked
        assert self.ship.scanner_locking_power_used is None
        assert self.ship.scanner_lock_target == "foobar"

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 500
        assert not self.ship.scanner_locking
        assert self.ship.scanner_locked
        assert self.ship.scanner_locking_power_used is None
        assert self.ship.scanner_lock_target == "foobar"

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.scanner_online
        assert self.ship.battery_power == 0
        assert not self.ship.scanner_locking
        assert self.ship.scanner_locked
        assert self.ship.scanner_locking_power_used is None
        assert self.ship.scanner_lock_target == "foobar"

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert not self.ship.scanner_online
        assert self.ship.battery_power == 0
        assert not self.ship.scanner_locking
        assert not self.ship.scanner_locked
        assert self.ship.scanner_locking_power_used is None
        assert self.ship.scanner_lock_target is None


    def test_ship_charging_ebeam_uses_resources(self):
        ''' EBEAM Charge '''
        self.ship.ebeam_charge_rate_per_second = 1000
        self.ship.ebeam_charge = 0
        self.ship.ebeam_charge_capacity = 10000
        self.ship.ebeam_firing = False
        self.ship.ebeam_charging = True
        self.ship.ebeam_charge_power_draw_multiple = 4
        self.ship.battery_power = 10000
        fps = 2

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.ebeam_charge == 500
        assert self.ship.battery_power == 8000
        assert self.ship.ebeam_charging

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.ebeam_charge == 1000
        assert self.ship.battery_power == 6000
        assert self.ship.ebeam_charging


    def test_ship_charging_ebeam_is_interrupted_if_not_enogh_battery_power(self):
        ''' EBEAM Charge '''
        self.ship.ebeam_charge_rate_per_second = 1000
        self.ship.ebeam_charge = 0
        self.ship.ebeam_charge_capacity = 10000
        self.ship.ebeam_firing = False
        self.ship.ebeam_charging = True
        self.ship.ebeam_charge_power_draw_multiple = 4
        self.ship.battery_power = 3000
        fps = 2

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.ebeam_charge == 500
        assert self.ship.battery_power == 1000
        assert self.ship.ebeam_charging

        self.ship.adjust_resources(fps=fps, game_frame=1) # Charging disabled, not enough power
        assert self.ship.ebeam_charge == 500
        assert self.ship.battery_power == 1000
        assert not self.ship.ebeam_charging


    def test_ship_charging_ebeam_is_interrupted_if_at_ebeam_charge_capacity(self):
        ''' EBEAM Charge '''
        self.ship.ebeam_charge_rate_per_second = 1000
        self.ship.ebeam_charge = 0
        self.ship.ebeam_charge_capacity = 750
        self.ship.ebeam_firing = False
        self.ship.ebeam_charging = True
        self.ship.ebeam_charge_power_draw_multiple = 4
        self.ship.battery_power = 10000
        fps = 2

        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.ebeam_charge == 500
        assert self.ship.battery_power == 8000
        assert self.ship.ebeam_charging

        self.ship.adjust_resources(fps=fps, game_frame=1) # Charging disabled, at capacity
        assert self.ship.ebeam_charge == 750
        assert self.ship.battery_power == 6000
        assert not self.ship.ebeam_charging
        self.ship.adjust_resources(fps=fps, game_frame=1)
        assert self.ship.ebeam_charge == 750
        assert self.ship.battery_power == 6000
        assert not self.ship.ebeam_charging



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

    def test_ship_v_over_150MS_immediatly_is_cut(self):
        self.fps = 10
        self.ship.velocity_x_meters_per_second = 300
        self.ship.velocity_y_meters_per_second = 120
        self.ship.gravity_brake_position = self.ship.gravity_brake_deployed_position
        self.ship.gravity_brake_active = True
        self._calculate_physics()
        assert self.ship.velocity_x_meters_per_second == 100
        assert self.ship.velocity_y_meters_per_second == 84
        # print(self.ship.velocity_x_meters_per_second)
        # print(self.ship.velocity_y_meters_per_second)

    def test_ship_comes_to_a_complete_stop(self):
        self.fps = 10
        self.ship.velocity_x_meters_per_second = 50
        self.ship.velocity_y_meters_per_second = 75
        self.ship.gravity_brake_position = self.ship.gravity_brake_deployed_position
        self.ship.gravity_brake_active = True
        self.ship.docking_at_station = "test-station-uuid"

        self._calculate_physics()
        assert self.ship.gravity_brake_active
        assert self.ship.docking_at_station == "test-station-uuid"
        assert self.ship.docked_at_station is None
        assert self.ship.velocity_x_meters_per_second == 35
        assert self.ship.velocity_y_meters_per_second == 52.5

        self._calculate_physics()
        assert self.ship.gravity_brake_active
        assert self.ship.docking_at_station == "test-station-uuid"
        assert self.ship.docked_at_station is None
        assert self.ship.velocity_x_meters_per_second == 24.5
        assert self.ship.velocity_y_meters_per_second == 36.75

        self._calculate_physics()
        assert self.ship.gravity_brake_active
        assert self.ship.docking_at_station == "test-station-uuid"
        assert self.ship.docked_at_station is None
        assert self.ship.velocity_x_meters_per_second == 17.15
        assert self.ship.velocity_y_meters_per_second == 25.725

        self._calculate_physics()
        assert self.ship.gravity_brake_active
        assert self.ship.docking_at_station == "test-station-uuid"
        assert self.ship.docked_at_station is None
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 12.00499)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 18.0075)

        self._calculate_physics()
        assert self.ship.gravity_brake_active
        assert self.ship.docking_at_station == "test-station-uuid"
        assert self.ship.docked_at_station is None
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 7.00499)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 12.6053)

        self._calculate_physics()
        assert self.ship.gravity_brake_active
        assert self.ship.docking_at_station == "test-station-uuid"
        assert self.ship.docked_at_station is None
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 7.6053)

        # Ship comes to a complete halt and grav brake is no longer active
        self._calculate_physics()
        assert not self.ship.gravity_brake_active
        assert self.ship.docking_at_station is None
        assert self.ship.docked_at_station == "test-station-uuid"
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0)
        print(self.ship.velocity_x_meters_per_second)
        print(self.ship.velocity_y_meters_per_second)

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
        # assert self.ship.heading_0_fin_0_rel_coord_0 == (-20, -20,) #TODO FIX ME
        # assert self.ship.heading_0_fin_0_rel_coord_1 == (-51, -40,)
        # assert self.ship.heading_0_fin_1_rel_coord_0 == (20, -20,)
        # assert self.ship.heading_0_fin_0_rel_coord_1 == (32, -40,)

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
        assert self.ship.engine_startup_power_used is None
        assert not self.ship.engine_starting
        self.ship.cmd_activate_engine()
        assert self.ship.engine_starting
        assert self.ship.engine_startup_power_used == 0

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

    def test_unlight_engine_command_updates_ship_state(self):
        self.ship.engine_online = True
        self.ship.engine_lit = True
        self.ship.cmd_unlight_engine()
        assert self.ship.engine_online
        assert not self.ship.engine_lit


""" ADVANCE DAMAGE PROPERTIES
"""

class TestShipAdvanceDamageProperties(TestCase):
    def setUp(self) -> None:
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=10)
        self.ship._seconds_to_explode = 2
        self.ship._seconds_to_aflame = 2
        self.ship.explode_immediately = False
        self.ship.coord_x = 25
        self.ship.coord_y = 30

    def test_an_undead_ship_does_not_change(self):
        self.ship.died_on_frame = None
        for i in range(10):
            self.ship.advance_damage_properties(i+1, 100, 100, 1)
        assert self.ship.died_on_frame is None
        assert self.ship.aflame_since_frame is None
        assert self.ship.explosion_frame is None
        assert self.ship.explosion_point is None

    def test_an_dead_ship_catches_fire_and_explodes(self):
        self.ship.died_on_frame = 1
        fps = 1
        self.ship.advance_damage_properties(1, 100, 100, fps)
        assert self.ship.died_on_frame == 1
        assert self.ship.aflame_since_frame is None
        assert self.ship.explosion_frame is None
        self.ship.advance_damage_properties(2, 100, 100, fps)
        assert self.ship.died_on_frame == 1
        assert self.ship.aflame_since_frame is None
        assert self.ship.explosion_frame is None
        self.ship.advance_damage_properties(3, 100, 100, fps)
        assert self.ship.died_on_frame == 1
        assert self.ship.aflame_since_frame is None
        assert self.ship.explosion_frame is None

        self.ship.advance_damage_properties(4, 100, 100, fps)
        assert self.ship.died_on_frame == 1
        assert self.ship.aflame_since_frame == 4 # Catch fire
        assert self.ship.explosion_frame is None
        self.ship.advance_damage_properties(5, 100, 100, fps)
        assert self.ship.died_on_frame == 1
        assert self.ship.aflame_since_frame == 4
        assert self.ship.explosion_frame is None
        self.ship.advance_damage_properties(6, 100, 100, fps)
        assert self.ship.died_on_frame == 1
        assert self.ship.aflame_since_frame == 4
        assert self.ship.explosion_frame is None
        assert self.ship.explosion_point is None

        self.ship.advance_damage_properties(7, 100, 100, fps) # Boom
        assert self.ship.died_on_frame == 1
        assert self.ship.aflame_since_frame is None
        assert self.ship.explosion_frame == 1
        assert self.ship.explosion_point == (25, 30,)
        self.ship.advance_damage_properties(8, 100, 100, fps)
        assert self.ship.died_on_frame == 1
        assert self.ship.aflame_since_frame is None
        assert self.ship.explosion_frame == 2
        self.ship.advance_damage_properties(9, 100, 100, fps)
        assert self.ship.died_on_frame == 1
        assert self.ship.aflame_since_frame is None
        assert self.ship.explosion_frame == 3

    def test_dead_ship_can_explode_immediatly(self):
        self.ship.explode_immediately = True
        self.ship.died_on_frame = 1
        fps = 1
        assert self.ship.explosion_frame is None
        assert self.ship.explosion_point is None
        self.ship.advance_damage_properties(1, 100, 100, fps)
        assert self.ship.explosion_frame == 1 # Boom
        assert self.ship.aflame_since_frame is None
        assert self.ship.explosion_point == (25, 30,)

    def test_dead_ship_explodes_if_it_goes_outside_map(self):
        self.ship.explode_immediately = False
        self.ship.died_on_frame = None
        fps = 1
        assert self.ship.explosion_frame is None
        assert self.ship.explosion_point is None
        self.ship.advance_damage_properties(1, 100, 100, fps)
        assert self.ship.died_on_frame is None
        assert self.ship.explosion_frame is None
        assert self.ship.explosion_point is None
        self.ship.advance_damage_properties(1, 10, 10, fps) # shrink map
        assert self.ship.died_on_frame is not None
        assert self.ship.explosion_frame == 1



""" Ship Thermal Signature
"""

class TestShipThermalSignature(TestCase):
    def setUp(self):
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=10)
        self.ship.coord_x = 25
        self.ship.coord_y = 30

        self.ship.fuel_level = 30_000
        self.ship.battery_power  = 500_000
        self.ship.scanner_thermal_signature = 0
        self.ship.scanner_thermal_signature_dissipation_per_second = 100
        self.ship.engine_lit_thermal_signature_rate_per_second = 400
        self.ship.ebeam_charge_thermal_signature_rate_per_second = 200
        self.ship.engine_boost_multiple = 25

    def test_thermal_signature_dissipates_to_zero(self):
        self.ship.scanner_thermal_signature = 1000
        self.ship.scanner_thermal_signature_dissipation_per_second = 400
        self.ship.advance_thermal_signature(fps=1)
        assert self.ship.scanner_thermal_signature == 600
        self.ship.advance_thermal_signature(fps=1)
        assert self.ship.scanner_thermal_signature == 200
        self.ship.advance_thermal_signature(fps=1)
        assert self.ship.scanner_thermal_signature == 0
        self.ship.advance_thermal_signature(fps=1)
        assert self.ship.scanner_thermal_signature == 0

    def test_thermal_signature_increases_due_to_engine_being_lit(self):
        self.ship.engine_lit = True
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 300
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 600

    def test_thermal_signature_increases_due_to_engine_being_boosted(self):
        self.ship.engine_lit = True
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 300
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 600
        self.ship.engine_boosted = True
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 10500

    def test_thermal_signature_increases_due_to_ebeam_charging(self):
        self.ship.ebeam_charging = True
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 100
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 200

    def test_thermal_signature_increases_due_to_ebeam_charging_and_engine_being_lit(self):
        self.ship.ebeam_charging = True
        self.ship.engine_lit = True
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 400
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 800

    def test_thermal_signature_increases_due_to_apu_running(self):
        self.ship.apu_starting = False
        self.ship.apu_online = True
        self.ship.fuel_level = 10_000
        self.ship.battery_power = 250
        self.ship.apu_online_thermal_signature_rate_per_second = 500
        self.ship.scanner_thermal_signature = 0
        self.ship.scanner_thermal_signature_dissipation_per_second = 100
        self.ship.advance_thermal_signature(fps=1)
        self.ship.scanner_thermal_signature == 400


""" ADVANCE DAMAGE PROPERTIES
"""

class TestShipAutopilot(TestCase):
    def setUp(self):
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=10)
        self.ship.coord_x = 25
        self.ship.coord_y = 30

    def test_autopilot_can_lock_onto_scanner_target(self):
        target_id = str(uuid4())
        self.ship.scanner_data[target_id] = {'relative_heading': 177}
        self.ship.scanner_lock_target = target_id
        self.ship.scanner_locking = False
        self.ship.scanner_locked = True
        self.ship.autopilot_program = AutoPilotPrograms.HEADING_LOCK_ON_TARGET
        self.ship.heading = 0
        self.ship.run_autopilot()
        assert self.ship.heading == 177

    def test_autopilot_can_lock_heading_prograde(self):
        self.ship.velocity_x_meters_per_second = 10 # Moving ENE
        self.ship.velocity_y_meters_per_second = 5  #
        self.ship.autopilot_program = AutoPilotPrograms.HEADING_LOCK_PROGRADE
        self.ship.heading = 0
        self.ship.run_autopilot()
        assert 90 > self.ship.heading > 45 # heading is ENE (prograde)

    def test_autopilot_can_lock_heading_retrograde(self):
        self.ship.velocity_x_meters_per_second = 10 # Moving ENE
        self.ship.velocity_y_meters_per_second = 5  #
        self.ship.autopilot_program = AutoPilotPrograms.HEADING_LOCK_RETROGRADE
        self.ship.heading = 0
        self.ship.run_autopilot()
        assert 270 > self.ship.heading > 225 # heading is WSW (retrograde)

    def test_autopilot_can_halt_the_ship(self):
        self.ship.velocity_x_meters_per_second = 4.0 # Moving NE
        self.ship.velocity_y_meters_per_second = 4.0 #
        self.ship.heading = 0
        self.ship.engine_lit = False
        self.ship.engine_online = True
        self.ship.engine_newtons = 1000
        self.ship._state[ShipStateKey.MASS] = 600
        self.ship.autopilot_program = AutoPilotPrograms.POSITION_HOLD

        self.ship.run_autopilot()
        assert self.ship.engine_lit is True
        assert self.ship.heading == 225 # Retrograde heading (SE)
        self.ship.calculate_physics(fps=6)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 3.80358)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.80358)

        self.ship.run_autopilot()
        assert self.ship.engine_lit is True
        assert self.ship.heading == 225 # Retrograde heading (SE)
        self.ship.calculate_physics(fps=6)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 3.60716)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.60716)

        self.ship.run_autopilot()
        assert self.ship.engine_lit is True
        assert self.ship.heading == 225 # Retrograde heading (SE)
        self.ship.calculate_physics(fps=6)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 3.41074)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 3.41074)

        self.ship.run_autopilot()
        assert self.ship.engine_lit is False
        assert self.ship.heading == 225
        self.ship.calculate_physics(fps=6)
        assert_floats_equal(self.ship.velocity_x_meters_per_second, 0)
        assert_floats_equal(self.ship.velocity_y_meters_per_second, 0)


''' ADVANCE GRAVITY BRAKE
'''
class TestShipAdjustGravityBrake(TestCase):
    def setUp(self):
        team_id = str(uuid4())
        self.ship = Ship.spawn(team_id, map_units_per_meter=10)
        self.ship.gravity_brake_position = 0
        self.ship.gravity_brake_deployed_position = 100
        self.ship.gravity_brake_traversal_per_second = 40

    def test_extend_gravity_brake(self):
        assert not self.ship.gravity_brake_deployed
        self.ship.gravity_brake_extending = True
        assert not self.ship.gravity_brake_deployed
        assert self.ship.gravity_brake_position == 0

        self.ship.advance_gravity_brake_position(fps=1)
        assert self.ship.gravity_brake_position == 40
        assert not self.ship.gravity_brake_deployed
        self.ship.advance_gravity_brake_position(fps=1)
        assert self.ship.gravity_brake_position == 80
        assert not self.ship.gravity_brake_deployed
        self.ship.advance_gravity_brake_position(fps=1)
        assert self.ship.gravity_brake_position == 100
        assert self.ship.gravity_brake_deployed


    def test_retract_gravity_brake(self):
        self.ship.gravity_brake_extending = False
        self.ship.gravity_brake_position = self.ship.gravity_brake_deployed_position
        assert self.ship.gravity_brake_deployed
        self.ship.gravity_brake_retracting = True

        self.ship.advance_gravity_brake_position(fps=1)
        assert self.ship.gravity_brake_position == 60
        assert not self.ship.gravity_brake_deployed
        self.ship.advance_gravity_brake_position(fps=1)
        assert self.ship.gravity_brake_position == 20
        self.ship.advance_gravity_brake_position(fps=1)
        assert self.ship.gravity_brake_position == 0
