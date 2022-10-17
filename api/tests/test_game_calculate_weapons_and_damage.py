

from uuid import uuid4
from unittest import TestCase

from api.models.game import Game, GamePhase, ShipScannerMode
from api import utils2d
from api.models.ship import VisibleElementShapeType, ScannedElementType
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

    def test_ebeam_fire_kills_a_target(self):
        # Arrange
        self.game._ships[self.player_1_ship_id].ebeam_charge = 8000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        assert self.game._ships[self.player_2_ship_id].died_on_frame is None
        # Act
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        # Assert
        assert self.game._ships[self.player_2_ship_id].died_on_frame == self.game._game_frame

    def test_killing_a_target_adds_a_row_to_the_kill_feed(self):
        # Arrange
        self.game._ships[self.player_1_ship_id].ebeam_charge = 8000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        assert self.game._ships[self.player_2_ship_id].died_on_frame is None
        assert len(self.game._killfeed) == 0
        # Act
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        # Assert
        assert len(self.game._killfeed) == 1

    def test_hitting_a_target_updates_the_shooters_ebeam_last_hit_frame_property(self):
        # Arrange
        self.game._game_frame = 1337
        self.game._ships[self.player_1_ship_id].ebeam_charge = 8000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        assert self.game._ships[self.player_2_ship_id].died_on_frame is None
        assert self.game._ships[self.player_1_ship_id].ebeam_last_hit_frame is None
        # Act
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        # Assert
        assert self.game._ships[self.player_1_ship_id].ebeam_last_hit_frame == 1337

    def test_killfeed_row_is_purged_after_8_seconds(self):
        self.game._game_frame = 1
        self.game._killfeed = [
            {
                "created_at_frame": 1,
                "victim_name": "foobar",
            }
        ]
        self.game._game_frame = 4
        self.game.purge_killfeed(fps=1)
        assert len(self.game._killfeed) == 1
        self.game._game_frame = 6
        self.game.purge_killfeed(fps=1)
        assert len(self.game._killfeed) == 1
        self.game._game_frame = 8
        self.game.purge_killfeed(fps=1)
        assert len(self.game._killfeed) == 1
        self.game._game_frame = 10
        self.game.purge_killfeed(fps=1)
        assert len(self.game._killfeed) == 0

    def test_ebeam_fire_misses_a_target(self):
        # Arrange
        self.game._ships[self.player_1_ship_id].ebeam_charge = 8000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH_WEST
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        assert self.game._ships[self.player_2_ship_id].died_on_frame is None
        # Act
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        # Assert
        assert self.game._ships[self.player_2_ship_id].died_on_frame is None

    def test_ebeam_rays_array_is_updated(self):
        # Arrange
        self.game._ships[self.player_1_ship_id].ebeam_charge = 8000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH_WEST
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        assert len(self.game._ebeam_rays) == 0
        # Act
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        # Assert
        assert len(self.game._ebeam_rays) == 1

    def test_firing_ebeam_ray_reduces_charge(self):
        # Arrange
        self.game._ships[self.player_1_ship_id].ebeam_charge = 8000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH_WEST
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        self.game._fps = 12
        # Act
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        # Assert
        assert self.game._ships[self.player_1_ship_id].ebeam_charge == 5083

    def test_ebeam_fire_shuts_off_when_ebeam_runs_out_of_charge(self):
        # Arrange
        self.game._ships[self.player_1_ship_id].ebeam_charge = 5000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH_WEST
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        self.game._fps = 12
        # Act
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].ebeam_charge == 2083
        assert self.game._ships[self.player_1_ship_id].ebeam_firing is True
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        # Assert
        assert self.game._ships[self.player_1_ship_id].ebeam_charge == 2083
        assert self.game._ships[self.player_1_ship_id].ebeam_firing is False

    def test_ebeam_does_not_fire_if_not_enough_charge(self):
        # Arrange
        self.game._ships[self.player_1_ship_id].ebeam_charge = 2000
        self.game._ships[self.player_1_ship_id].coord_x = 1000
        self.game._ships[self.player_1_ship_id].coord_y = 1000
        self.game._ships[self.player_1_ship_id].heading = constants.DEGREES_NORTH
        self.game._ships[self.player_1_ship_id].ebeam_firing = True
        self.game._ships[self.player_2_ship_id].coord_x = 1000
        self.game._ships[self.player_2_ship_id].coord_y = 6000
        assert self.game._ships[self.player_2_ship_id].died_on_frame is None
        self.game._fps = 12
        # Act
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        # Assert
        assert self.game._ships[self.player_2_ship_id].died_on_frame is None
        assert self.game._ships[self.player_1_ship_id].ebeam_firing is False


    def test_ship_explodes_if_it_goes_outside_the_map(self):
        pass


    def test_ship_explodes_if_it_collides_with_mining_location(self):
        pass


    def test_ship_explodes_if_it_collides_with_space_station(self):
        pass

