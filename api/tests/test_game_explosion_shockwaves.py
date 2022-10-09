

from uuid import uuid4
from unittest import TestCase

from api.models.game import Game, GamePhase#, ShipScannerMode
# from api import utils2d
# from api.models.ship import VisibleElementShapeType, ScannedElementType
from api import constants

class TestEBeamAndDamage(TestCase):
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
                "meters_x": 100 * 1000, # 100KM
                "meters_y": 100 * 1000, # 100KM
                "name": "TestMap",
            },
            'spawnPoints': [{
                'position_meters_x': 100,
                'position_meters_y': 100,
            },{
                'position_meters_x': 200,
                'position_meters_y': 200,
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
        assert isinstance(self.game._game_frame, int)

    def test_exploding_a_ship_creates_an_explosion_shockwave(self):
        # Arrange
        self.game._ships[self.player_1_ship_id].ebeam_charge = 8000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        self.game._ships[self.player_2_ship_id].explode_immediately = True
        self.game._game_frame = 10
        assert self.game._ships[self.player_2_ship_id].died_on_frame is None
        assert len(self.game._explosion_shockwaves) == 0
        # Act
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        self.game.calculate_weapons_and_damage(self.player_2_ship_id)
        # Assert
        assert self.game._ships[self.player_1_ship_id].died_on_frame is None
        assert self.game._ships[self.player_2_ship_id].died_on_frame == self.game._game_frame
        assert len(self.game._explosion_shockwaves) == 1
        assert self.game._explosion_shockwaves[0]['origin_point'] == self.game._ships[self.player_2_ship_id].coords
        assert self.game._explosion_shockwaves[0]['radius_meters'] == 1

    def test_game_advances_explosion_shock_wave(self):
        # Arrange
        self.game._ships[self.player_1_ship_id].ebeam_charge = 8000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        self.game._ships[self.player_2_ship_id].explode_immediately = True
        self.game._game_frame = 10
        assert self.game._ships[self.player_2_ship_id].died_on_frame is None
        assert len(self.game._explosion_shockwaves) == 0
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        self.game.calculate_weapons_and_damage(self.player_2_ship_id)
        assert self.game._ships[self.player_1_ship_id].died_on_frame is None
        assert self.game._ships[self.player_2_ship_id].died_on_frame == self.game._game_frame
        assert len(self.game._explosion_shockwaves) == 1
        assert self.game._explosion_shockwaves[0]['radius_meters'] == 1
        # ACT
        self.game.advance_explosion_shockwaves()
        # Assert
        assert self.game._explosion_shockwaves[0]['radius_meters'] > 1
