


# These tests are absolutely horrible Dx

from uuid import uuid4

from unittest import TestCase

from api.models.game import Game, GamePhase
from api.constants import EMP_SLUG


class TestTubeWeapons(TestCase):

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
        self.game._ships[self.player_1_ship_id].recoilless_tube_launches = False
        self.game._ships[self.player_2_ship_id].recoilless_tube_launches = False
        self.game._ships[self.player_1_ship_id].special_weapons_tubes_count = 1
        self.game._ships[self.player_2_ship_id].special_weapons_tubes_count = 1
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 100000
        self.game._ships[self.player_2_ship_id].virtual_ore_kg = 100000
        self.game._special_weapon_costs[EMP_SLUG] = 200
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 0
        self.game._ships[self.player_2_ship_id].magnet_mines_loaded = 0
        self.game._ships[self.player_1_ship_id].emps_loaded = 1
        self.game._ships[self.player_2_ship_id].emps_loaded = 1
        self.game._ships[self.player_1_ship_id].hunter_drones_loaded = 0
        self.game._ships[self.player_2_ship_id].hunter_drones_loaded = 0

    def test_launching_weapon_north_east_causes_recoil_to_south_west(self):
        assert self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second == 0
        assert self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second == 0
        self.game._ships[self.player_1_ship_id]._set_heading(45)
        self.game._ships[self.player_1_ship_id].cmd_launch_emp()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second < 0
        assert self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second < 0


    def test_launching_weapon_south_west_causes_recoil_to_north_east(self):
        assert self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second == 0
        assert self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second == 0
        self.game._ships[self.player_1_ship_id]._set_heading(180 + 45)
        self.game._ships[self.player_1_ship_id].cmd_launch_emp()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second > 0
        assert self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second > 0
