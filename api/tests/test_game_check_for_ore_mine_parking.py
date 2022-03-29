
from uuid import uuid4
from unittest import TestCase

from api.models.game import Game, GamePhase


class TestGameCheckForOreMineParking(TestCase):

    def setUp(self):
        # MAP UNITS PER METER
        self.upm = 10

        self.ore_mine_id = str(uuid4())

        self.player_1_id = str(uuid4())
        self.player_1_handle = "foobar"
        self.player_1_ship_id = None
        self.player_1_team_id = str(uuid4())
        self.player_2_id = str(uuid4())
        self.player_2_handle = "derpy"
        self.player_2_ship_id = None
        self.player_2_team_id = str(uuid4())

        self.game = Game()

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
                "meters_x": 1 * 1000, # 1KM
                "meters_y": 1 * 1000, # 1KM
                "name": "TestMap",
            },
            'spawnPoints': [{
                'position_meters_x': 100,
                'position_meters_y': 100,
            },{
                'position_meters_x': 900,
                'position_meters_y': 900,
            }],
            'spaceStations': [],
            'miningLocations': [             {
                "position_meters_x": 500,
                "position_meters_y": 500,
                "service_radius_meters": 100,
                "starting_ore_amount_kg": 700,
                "name": "test-station",
                "uuid": self.ore_mine_id,
            }],
        }, map_units_per_meter=self.upm)
        assert self.game.map_is_configured

        self.game.advance_to_phase_1_starting()
        self.player_1_ship_id = self.game._player_id_to_ship_id_map[self.player_1_id]
        self.player_2_ship_id = self.game._player_id_to_ship_id_map[self.player_2_id]
        self.game._game_start_countdown = 1
        self.game.decr_phase_1_starting_countdown()
        assert self.game._phase == GamePhase.LIVE
        self.game._game_frame = 3

    def test_ship_parks_if_stationary_near_mine(self):
        # Place ship near mine
        self.game._ships[self.player_1_ship_id].coord_x = 570 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 570 * self.upm
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].parked_at_ore_mine = None
        self.game.check_for_ore_mine_parking(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].parked_at_ore_mine == self.ore_mine_id

    def test_ship_does_not_park_if_stationary_not_near_mine(self):
        # Place ship outside service perimeter
        self.game._ships[self.player_1_ship_id].coord_x = 610 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].parked_at_ore_mine = None
        self.game.check_for_ore_mine_parking(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].parked_at_ore_mine is None

    def test_ship_does_not_park_if_ship_is_not_stationary(self):
        # Place ship near mine, but give it velocity
        self.game._ships[self.player_1_ship_id].coord_x = 570 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 570 * self.upm
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 1
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 1
        self.game._ships[self.player_1_ship_id].parked_at_ore_mine = None
        self.game.check_for_ore_mine_parking(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].parked_at_ore_mine is None
