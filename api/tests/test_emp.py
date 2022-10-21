
from uuid import uuid4

from unittest import TestCase

from api.models.game import Game, GamePhase
from api.constants import EMP_SLUG


class TestEMP(TestCase):

    def setUp(self):
        # MAP UNITS PER METER
        self.upm = 10

        self.player_1_id = str(uuid4())
        self.player_1_handle = "foobar"
        self.player_1_ship_id = None
        self.player_1_team_id = str(uuid4())
        self.player_2_id = str(uuid4())
        self.player_2_handle = "derpy"
        self.player_2_ship_id = None
        self.player_2_team_id = str(uuid4())

        self.game = Game()
        self.game._fps = 1
        self.game._is_testing = True

        self.game.register_player({
            'player_id':self.player_1_id,
            'player_name': self.player_1_handle,
            'team_id': self.player_1_team_id,
        })
        self.game.register_player({
            'player_id':self.player_2_id,
            'player_name': self.player_2_handle,
            'team_id': self.player_2_team_id,
        })

        self.game.set_map({
            'mapData':{
                "meters_x": 3 * 1000, # 3KM
                "meters_y": 3 * 1000, # 3KM
                "name": "TestMap",
            },
            'spawnPoints': [{
                'position_meters_x': 100,
                'position_meters_y': 100,
            },{
                'position_meters_x': 2900,
                'position_meters_y': 2900,
            }],
            'spaceStations': [],
            'miningLocations': [],
        }, map_units_per_meter=self.upm)
        assert self.game.map_is_configured

        self.game.advance_to_phase_1_starting()
        self.player_1_ship_id = self.game._player_id_to_ship_id_map[self.player_1_id]
        self.player_2_ship_id = self.game._player_id_to_ship_id_map[self.player_2_id]
        self.game._game_start_countdown = 1
        self.game.decr_phase_1_starting_countdown()
        assert self.game._phase == GamePhase.LIVE
        self.game._game_frame = 3
        self.game._ships[self.player_1_ship_id].special_weapons_tubes_count = 1
        self.game._ships[self.player_2_ship_id].special_weapons_tubes_count = 1
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 1000
        self.game._ships[self.player_2_ship_id].virtual_ore_kg = 1000
        self.game._special_weapon_costs[EMP_SLUG] = 200
        self.game._ships[self.player_1_ship_id].emps_loaded = 0
        self.game._ships[self.player_2_ship_id].emps_loaded = 0
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 0
        self.game._ships[self.player_2_ship_id].magnet_mines_loaded = 0

    def test_ship_can_buy_emp_if_tube_available(self):
        assert self.game._ships[self.player_1_ship_id]
        assert self.game._ships[self.player_1_ship_id].emps_loaded == 0
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_emp()
        assert self.game._ships[self.player_1_ship_id].emps_loaded == 1
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 0
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 800

    def test_ship_cannot_buy_emp_if_not_enough_ore(self):
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 100 # Not enough.
        assert self.game._ships[self.player_1_ship_id].emps_loaded == 0
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_emp()
        assert self.game._ships[self.player_1_ship_id].emps_loaded == 0

    def test_ship_cannot_buy_magnet_mine_if_not_enough_tubes(self):
        self.game._ships[self.player_1_ship_id].special_weapons_tubes_count = 1
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 1000
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 1
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_emp()
        assert self.game._ships[self.player_1_ship_id].emps_loaded == 0
        # double check
        self.game._ships[self.player_1_ship_id].special_weapons_tubes_count += 1
        self.game._ships[self.player_1_ship_id].cmd_buy_emp()
        assert self.game._ships[self.player_1_ship_id].emps_loaded == 1

    def test_ship_cannot_buy_magnet_mine_if_not_docked_at_station(self):
        assert self.game._ships[self.player_1_ship_id].emps_loaded == 0
        self.game._ships[self.player_1_ship_id].cmd_buy_emp()
        assert self.game._ships[self.player_1_ship_id].emps_loaded == 0
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_emp()
        assert self.game._ships[self.player_1_ship_id].emps_loaded == 1
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 800

    def test_ship_can_launch_a_emp_due_east_from_stationary_positon(self):
        assert len(self.game._emps) == 0
        # ship 1 at 100, 100 meters
        self.game._ships[self.player_1_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_1_ship_id].coord_y = 100 * 10
        # ship 2 1KM north at 100, 1100 meters
        self.game._ships[self.player_2_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_2_ship_id].coord_y = 1100 * 10

        self.game._fps = 1
        self.game._ships[self.player_1_ship_id].emps_loaded = 1
        self.game._ships[self.player_1_ship_id].heading = 90
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        # Fire mine
        self.game._ships[self.player_1_ship_id].cmd_launch_emp(
            launch_velocity=10
        )
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._emps) == 1
        emp_id = next(iter(self.game._emps.keys()))
        emp = self.game._emps[emp_id]

        assert emp.ship_id == self.player_1_ship_id
        assert emp.elapsed_milliseconds == 0
        assert not emp.armed
        assert not emp.exploded
        assert emp.velocity_x_meters_per_second == 10
        assert round(emp.velocity_y_meters_per_second, 5) == 0
        assert emp.coord_x == 1000
        assert emp.coord_y == 1060 # Front of the ship

        self.game.advance_emps(fps=1)
        assert not emp.armed
        assert not emp.exploded
        assert emp.velocity_x_meters_per_second == 10 # no acceleration
        assert round(emp.velocity_y_meters_per_second, 5) == 0
        assert round(emp.coord_x) == 1100
        assert emp.coord_y == 1060
        assert emp.elapsed_milliseconds == 1000 # 1 second has elapsed

    def test_ship_can_launch_an_EMP_due_east_with_northward_ship_movement(self):
        assert len(self.game._emps) == 0
        # ship 1 at 100, 100 meters
        self.game._ships[self.player_1_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_1_ship_id].coord_y = 100 * 10
        # ship 2 1KM north at 100, 1100 meters
        self.game._ships[self.player_2_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_2_ship_id].coord_y = 1100 * 10

        self.game._fps = 1
        self.game._ships[self.player_1_ship_id].emps_loaded = 1
        self.game._ships[self.player_1_ship_id].heading = 90
        # ship moving north at 5 M/S
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 5
        # Fire mine
        self.game._ships[self.player_1_ship_id].cmd_launch_emp(
            launch_velocity=10
        )
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)

        assert len(self.game._emps) == 1
        emp_id = next(iter(self.game._emps.keys()))
        emp = self.game._emps[emp_id]
        assert emp.elapsed_milliseconds == 0
        assert not emp.armed
        assert not emp.exploded
        # from tube launch
        assert emp.velocity_x_meters_per_second == 10
        # from ships innertia
        assert round(emp.velocity_y_meters_per_second, 5) == 5
        assert emp.coord_x == 1000
        assert emp.coord_y == 1060

        self.game.advance_emps(fps=1)
        emp = self.game._emps[emp_id]
        assert not emp.armed
        assert not emp.exploded
        assert emp.velocity_x_meters_per_second == 10 # no acceleration
        assert round(emp.velocity_y_meters_per_second, 5) == 5
        assert emp.coord_x == 1100
        assert emp.coord_y == 1110
        assert emp.elapsed_milliseconds == 1000 # 1 second has elapsed
