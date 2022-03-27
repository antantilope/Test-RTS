
from typing import Tuple
from unittest import TestCase
from uuid import uuid4

from api.models.game import Game, GamePhase
from api import constants

class TestGravityBrakeCatchingLogic(TestCase):

    def setUp(self):
        self.upm = 10
        self.player_1_id = str(uuid4())
        self.player_1_handle = "foobar"
        self.player_1_ship_id = None
        self.player_1_team_id = str(uuid4())
        self.player_2_id = str(uuid4())
        self.player_2_handle = "derpy"
        self.player_2_ship_id = None
        self.player_2_team_id = str(uuid4())

        self.station_id = "9e622cae-ad69-4074-88f0-50876430fd3e"

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
            'spaceStations': [
                {
                    "position_meters_x": 500,
                    "position_meters_y": 500,
                    "service_radius_meters": 100,
                    "name": "test-station",
                    "uuid": self.station_id,
                }
            ],
            'miningLocations': [],
        }, map_units_per_meter=self.upm)
        assert self.game.map_is_configured

        self.game.advance_to_phase_1_starting()
        self.player_1_ship_id = self.game._player_id_to_ship_id_map[self.player_1_id]
        self.player_2_ship_id = self.game._player_id_to_ship_id_map[self.player_2_id]
        self.game._game_start_countdown = 1
        self.game.decr_phase_1_starting_countdown()
        assert self.game._phase == GamePhase.LIVE


    def get_ship_id_at_coords(self, coords: Tuple[int]):
        for id, ship in self.game._ships.items():
            if (ship.coords == coords):
                return id

    def test_grav_brake_activates_when_ship_with_deployed_brake_flies_through_service_radius(self):
        self.game._ships[self.player_1_ship_id].gravity_brake_position = self.game._ships[self.player_1_ship_id].gravity_brake_deployed_position
        self.game._ships[self.player_1_ship_id].gravity_brake_active = False
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 30
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 30
        self.game.check_for_gravity_brake_catch(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].gravity_brake_active is False
        # Move ship into service radius and the brake catches.
        self.game._ships[self.player_1_ship_id].coord_x = 5500
        self.game._ships[self.player_1_ship_id].coord_y = 5500
        self.game.check_for_gravity_brake_catch(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].gravity_brake_active is True
        assert self.game._ships[self.player_1_ship_id].docking_at_station == self.station_id
        assert self.game._ships[self.player_1_ship_id].docked_at_station is None

    def test_grav_brake_does_not_activates_when_ship_with_retracted_brake_flies_through_service_radius(self):
        # brake not fully deployed.
        self.game._ships[self.player_1_ship_id].gravity_brake_position = self.game._ships[self.player_1_ship_id].gravity_brake_deployed_position - 1
        self.game._ships[self.player_1_ship_id].gravity_brake_active = False
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 30
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 30
        self.game.check_for_gravity_brake_catch(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].gravity_brake_active is False
        # Move ship into service radius and the brake does not  catches.
        self.game._ships[self.player_1_ship_id].coord_x = 5500
        self.game._ships[self.player_1_ship_id].coord_y = 5500
        self.game.check_for_gravity_brake_catch(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].gravity_brake_active is False
        assert self.game._ships[self.player_1_ship_id].docking_at_station is None
        assert self.game._ships[self.player_1_ship_id].docked_at_station is None

    def test_engine_is_unlit_when_ship_with_deployed_brake_flies_through_service_radius(self):
        self.game._ships[self.player_1_ship_id].gravity_brake_position = self.game._ships[self.player_1_ship_id].gravity_brake_deployed_position
        self.game._ships[self.player_1_ship_id].gravity_brake_active = False
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 30
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 30
        self.game._ships[self.player_1_ship_id].engine_lit = True
        self.game._ships[self.player_1_ship_id].engine_online = True
        self.game.check_for_gravity_brake_catch(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].gravity_brake_active is False
        # Move ship into service radius and the brake catches.
        self.game._ships[self.player_1_ship_id].coord_x = 5500
        self.game._ships[self.player_1_ship_id].coord_y = 5500
        self.game.check_for_gravity_brake_catch(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].gravity_brake_active is True
        assert self.game._ships[self.player_1_ship_id].engine_lit is False # engine unlights
        assert self.game._ships[self.player_1_ship_id].engine_online is True
