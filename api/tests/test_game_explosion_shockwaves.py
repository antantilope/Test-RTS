

from uuid import uuid4
from unittest import TestCase

from api.models.game import Game, GamePhase
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

    def test_explosion_shock_wave_instantly_accelerates_nearby_ship(self):
        self.game._fps = 1
        assert self.game._map_units_per_meter == 10
        self.game._is_testing = True
        self.game._shockwave_max_delta_v_meters_per_second = 20
        self.game._shockwave_max_delta_v_coef = -0.000005
        self.game._explosion_shockwave_max_radius_meters = 4000
        # place stationary ship at 500M, 500M
        self.game._ships[self.player_1_ship_id].coord_x = 5000
        self.game._ships[self.player_1_ship_id].coord_y = 5000

        # remove ship 2, don't care about it for this test.
        del self.game._ships[self.player_2_ship_id]

        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        # Create an explosion at the origin point (0, 0)
        # due south west of the ship
        assert len(self.game._explosion_shockwaves) == 0
        self.game.register_explosion_on_map((0, 0), 60, 4000, 4000)
        assert len(self.game._explosion_shockwaves) == 1
        swid = self.game._explosion_shockwaves[0]['id']
        assert self.game._explosion_shockwaves[0]['origin_point'] == (0, 0)
        assert self.game._explosion_shockwaves[0]['radius_meters'] == 1

        self.game.advance_explosion_shockwaves()
        assert self.game._explosion_shockwaves[0]['radius_meters'] == constants.SPEED_OF_SOUND_METERS_PER_SECOND + 1
        assert self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second == 0
        assert self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second == 0
        assert self.player_1_ship_id not in self.game._ships_hit_by_shockwave[swid]

        self.game.advance_explosion_shockwaves()
        assert self.game._explosion_shockwaves[0]['radius_meters'] == 2*constants.SPEED_OF_SOUND_METERS_PER_SECOND + 1
        assert self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second == 0
        assert self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second == 0
        assert self.player_1_ship_id not in self.game._ships_hit_by_shockwave[swid]

        # ship is overtaken by shockwave and accelerated
        self.game.advance_explosion_shockwaves()
        assert round(self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second) == 12
        assert round(self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second) == 12
        assert self.player_1_ship_id in self.game._ships_hit_by_shockwave[swid]
        self.game.advance_explosion_shockwaves()
        assert round(self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second) == 12
        assert round(self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second) == 12
        assert self.player_1_ship_id in self.game._ships_hit_by_shockwave[swid]
