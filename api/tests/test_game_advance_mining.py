
from uuid import uuid4
from unittest import TestCase

from api.models.game import Game, GamePhase
from api import utils2d
from api.models.ship import Ship
from .utils import assert_floats_equal


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
        self.game._fps = 2

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

        # Place ship near mine and park it.
        self.game._ships[self.player_1_ship_id].coord_x = 570 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 570 * self.upm
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game.check_for_ore_mine_parking(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].parked_at_ore_mine == self.ore_mine_id

        # Set mining attributes for this test
        self.game._ships[self.player_1_ship_id].battery_power = 200_000
        self.game._ships[self.player_1_ship_id].mining_ore = False
        self.game._ships[self.player_1_ship_id].cargo_ore_mass_capacity_kg = 100
        self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg = 0
        self.game._ships[self.player_1_ship_id].mining_ore_power_usage_per_second = 50
        self.game._ships[self.player_1_ship_id].mining_ore_kg_collected_per_second = 15


    def test_mining_increases_cargo_ore_mass_kg_and_removes_mass_from_mine(self):
        assert self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg == 0
        self.game._ships[self.player_1_ship_id].mining_ore = True
        self.game.advance_mining(self.player_1_ship_id)
        assert_floats_equal(self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg, 7.5)
        assert_floats_equal(self.game._ore_mines_remaining_ore[self.ore_mine_id], 700 - 7.5)
        assert self.game._ships[self.player_1_ship_id].mining_ore

    def test_not_mining_does_not_increases_cargo_ore_mass_kg(self):
        assert self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg == 0
        self.game._ships[self.player_1_ship_id].mining_ore = False
        self.game.advance_mining(self.player_1_ship_id)
        assert_floats_equal(self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg, 0)
        assert not self.game._ships[self.player_1_ship_id].mining_ore

    def test_mining_stops_if_ship_hits_ore_mass_capacity(self):
        self.game._ships[self.player_1_ship_id].cargo_ore_mass_capacity_kg = 10
        self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg = 0
        self.game._ships[self.player_1_ship_id].mining_ore = True
        # grab full scope on this frame.
        self.game.advance_mining(self.player_1_ship_id)
        assert_floats_equal(self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg, 7.5)
        assert self.game._ships[self.player_1_ship_id].mining_ore
        # top off
        self.game.advance_mining(self.player_1_ship_id)
        assert_floats_equal(self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg, 10.0)
        assert self.game._ships[self.player_1_ship_id].mining_ore
        # No room
        self.game.advance_mining(self.player_1_ship_id)
        assert_floats_equal(self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg, 10.0)
        assert not self.game._ships[self.player_1_ship_id].mining_ore

    def test_mining_stops_if_ore_mine_is_depleted(self):
        self.game._ore_mines_remaining_ore[self.ore_mine_id] = 10
        self.game._ships[self.player_1_ship_id].cargo_ore_mass_capacity_kg = 100
        self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg = 0
        self.game._ships[self.player_1_ship_id].mining_ore = True
        # grab full scope on this frame.
        self.game.advance_mining(self.player_1_ship_id)
        assert_floats_equal(self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg, 7.5)
        assert_floats_equal(self.game._ore_mines_remaining_ore[self.ore_mine_id], 2.5)
        assert self.game._ships[self.player_1_ship_id].mining_ore
        # get last bit from the mine
        self.game.advance_mining(self.player_1_ship_id)
        assert_floats_equal(self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg, 10.0)
        assert_floats_equal(self.game._ore_mines_remaining_ore[self.ore_mine_id], 0)
        assert self.game._ships[self.player_1_ship_id].mining_ore
        # Mine depleted
        self.game.advance_mining(self.player_1_ship_id)
        assert_floats_equal(self.game._ships[self.player_1_ship_id].cargo_ore_mass_kg, 10.0)
        assert not self.game._ships[self.player_1_ship_id].mining_ore
        assert_floats_equal(self.game._ore_mines_remaining_ore[self.ore_mine_id], 0)
