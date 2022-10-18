
from uuid import uuid4

from unittest import TestCase

from api.models.game import Game, GamePhase
from api.constants import MAGNET_MINE_SLUG


class TestMagnetMine(TestCase):

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
        self.game._special_weapon_costs[MAGNET_MINE_SLUG] = 200

    def test_ship_can_buy_magnet_mine_if_tube_available(self):
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 0
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_magnet_mine()
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 1
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 800

    def test_ship_cannot_buy_magnet_mine_if_not_enough_ore(self):
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 100 # Not enough.
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 0
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_magnet_mine()
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 0

    def test_ship_cannot_buy_magnet_mine_if_not_enough_tubes(self):
        self.game._ships[self.player_1_ship_id].special_weapons_tubes_count = 1
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 1000
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 1
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_magnet_mine()
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 1
        # double check
        self.game._ships[self.player_1_ship_id].special_weapons_tubes_count += 1
        self.game._ships[self.player_1_ship_id].cmd_buy_magnet_mine()
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 2

    def test_ship_cannot_buy_magnet_mine_if_not_docked_at_station(self):
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 0
        self.game._ships[self.player_1_ship_id].cmd_buy_magnet_mine()
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 0
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_magnet_mine()
        assert self.game._ships[self.player_1_ship_id].magnet_mines_loaded == 1
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 800

    def test_ship_can_launch_a_magnet_mine_due_east_from_stationary_positon(self):
        assert len(self.game._magnet_mines) == 0
        # ship 1 at 100, 100 meters
        self.game._ships[self.player_1_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_1_ship_id].coord_y = 100 * 10
        # ship 2 1KM north at 100, 1100 meters
        self.game._ships[self.player_2_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_2_ship_id].coord_y = 1100 * 10

        self.game._fps = 1
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 1
        self.game._ships[self.player_1_ship_id].heading = 90
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        # Fire mine
        self.game._ships[self.player_1_ship_id].cmd_launch_magnet_mine(
            launch_velocity=10
        )
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._magnet_mines) == 1
        mine_id = next(iter(self.game._magnet_mines.keys()))
        mine = self.game._magnet_mines[mine_id]
        assert mine.ship_id == self.player_1_ship_id
        assert mine.elapsed_milliseconds == 0
        assert not mine.armed
        assert not mine.exploded
        assert mine.closest_ship_id is None
        assert mine.distance_to_closest_ship is None
        assert mine.velocity_x_meters_per_second == 10
        assert round(mine.velocity_y_meters_per_second, 5) == 0
        assert mine.coord_x == 1000
        assert mine.coord_y == 1000

        self.game.advance_magnet_mines(fps=1)
        mine = self.game._magnet_mines[mine_id]
        assert not mine.armed
        assert not mine.exploded
        assert mine.closest_ship_id is None
        assert mine.distance_to_closest_ship is None
        assert mine.velocity_x_meters_per_second == 10 # no acceleration yet
        assert round(mine.velocity_y_meters_per_second, 5) == 0
        assert mine.coord_x == 1100
        assert mine.coord_y == 1000
        assert mine.elapsed_milliseconds == 1000 # 1 second has elapsed

    def test_ship_can_launch_a_magnet_mine_due_east_with_northward_ship_movement(self):
        assert len(self.game._magnet_mines) == 0
        # ship 1 at 100, 100 meters
        self.game._ships[self.player_1_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_1_ship_id].coord_y = 100 * 10
        # ship 2 1KM north at 100, 1100 meters
        self.game._ships[self.player_2_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_2_ship_id].coord_y = 1100 * 10

        self.game._fps = 1
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 1
        self.game._ships[self.player_1_ship_id].heading = 90
        # ship moving north at 5 M/S
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 5
        # Fire mine
        self.game._ships[self.player_1_ship_id].cmd_launch_magnet_mine(
            launch_velocity=10
        )
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)

        assert len(self.game._magnet_mines) == 1
        mine_id = next(iter(self.game._magnet_mines.keys()))
        mine = self.game._magnet_mines[mine_id]
        assert mine.elapsed_milliseconds == 0
        assert not mine.armed
        assert not mine.exploded
        assert mine.closest_ship_id is None
        assert mine.distance_to_closest_ship is None
        # from tube launch
        assert mine.velocity_x_meters_per_second == 10
        # from ships innertia
        assert round(mine.velocity_y_meters_per_second, 5) == 5
        assert mine.coord_x == 1000
        assert mine.coord_y == 1000

        self.game.advance_magnet_mines(fps=1)
        mine = self.game._magnet_mines[mine_id]
        assert not mine.armed
        assert not mine.exploded
        assert mine.closest_ship_id is None
        assert mine.distance_to_closest_ship is None
        assert mine.velocity_x_meters_per_second == 10 # no acceleration yet
        assert round(mine.velocity_y_meters_per_second, 5) == 5
        assert mine.coord_x == 1100
        assert mine.coord_y == 1050
        assert mine.elapsed_milliseconds == 1000 # 1 second has elapsed

    def test_mine_arms_after_arming_time_runs_out(self):
        self.game._magnet_mine_arming_time_seconds = 3
        self.game._magnet_mine_tracking_acceleration_ms = 25
        assert len(self.game._magnet_mines) == 0
        # ship 1 at 100, 100 meters
        self.game._ships[self.player_1_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_1_ship_id].coord_y = 100 * 10
        # ship 2 1KM north at 100, 1100 meters
        self.game._ships[self.player_2_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_2_ship_id].coord_y = 1100 * 10

        self.game._fps = 1
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 1
        self.game._ships[self.player_1_ship_id].heading = 90
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        # Fire mine
        self.game._ships[self.player_1_ship_id].cmd_launch_magnet_mine(
            launch_velocity=10
        )
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._magnet_mines) == 1
        mine_id = next(iter(self.game._magnet_mines.keys()))
        mine = self.game._magnet_mines[mine_id]
        assert mine.elapsed_milliseconds == 0
        assert not mine.armed

        self.game.advance_magnet_mines(fps=2)
        assert mine.elapsed_milliseconds == 500
        assert not mine.armed
        self.game.advance_magnet_mines(fps=2)
        assert mine.elapsed_milliseconds == 1000
        assert not mine.armed
        self.game.advance_magnet_mines(fps=2)
        assert mine.elapsed_milliseconds == 1500
        assert not mine.armed
        self.game.advance_magnet_mines(fps=2)
        assert mine.elapsed_milliseconds == 2000
        assert not mine.armed
        self.game.advance_magnet_mines(fps=2)
        assert mine.elapsed_milliseconds == 2500
        assert not mine.armed
        self.game.advance_magnet_mines(fps=2)
        assert mine.elapsed_milliseconds == 3000
        assert not mine.armed
        self.game.advance_magnet_mines(fps=2)
        assert mine.elapsed_milliseconds == 3500
        assert mine.armed        # Mine has armed
        assert not mine.exploded # and not exploded yet.

    def test_mine_accelerates_towards_closest_ship_after_arming(self):
        self.game._fps = 1
        self.game._magnet_mine_arming_time_seconds = 3
        self.game._magnet_mine_tracking_acceleration_ms = 25
        assert len(self.game._magnet_mines) == 0
        # ship 1 at 100, 100 meters
        self.game._ships[self.player_1_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_1_ship_id].coord_y = 100 * 10
        self.game._ships[self.player_1_ship_id].heading = 0
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 1
        # ship 2 500M north at 100, 600 meters
        self.game._ships[self.player_2_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_2_ship_id].coord_y = 600 * 10

        # Fire mine due north
        # moving at 100M/S, arming after 3 seconds.
        # mine will be 200 meters from ship 2
        # mine will be 300 meters from ship 1
        # mine should target ship 2
        self.game._ships[self.player_1_ship_id].cmd_launch_magnet_mine(
            launch_velocity=100
        )
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._magnet_mines) == 1
        mine_id = next(iter(self.game._magnet_mines.keys()))
        mine = self.game._magnet_mines[mine_id]
        assert mine.elapsed_milliseconds == 0
        assert not mine.armed
        assert mine.velocity_y_meters_per_second == 100
        self.game.advance_magnet_mines(fps=1)
        assert mine.elapsed_milliseconds == 1000
        assert not mine.armed
        assert mine.coord_x == 1000
        assert mine.coord_y == 2000
        assert mine.velocity_y_meters_per_second == 100
        self.game.advance_magnet_mines(fps=1)
        assert mine.elapsed_milliseconds == 2000
        assert not mine.armed
        assert mine.coord_x == 1000
        assert mine.coord_y == 3000
        assert mine.velocity_y_meters_per_second == 100
        self.game.advance_magnet_mines(fps=1)
        assert mine.elapsed_milliseconds == 3000
        assert not mine.armed
        assert mine.coord_y == 4000
        assert mine.velocity_y_meters_per_second == 100
        self.game.advance_magnet_mines(fps=1)
        assert mine.elapsed_milliseconds == 4000
        assert mine.armed
        assert mine.closest_ship_id == self.player_2_ship_id
        # mine accelerates once
        assert mine.coord_y == 5250
        assert mine.velocity_y_meters_per_second == 125

    def test_mine_explodes_if_get_gets_within_proximity_of_ship(self):
        self.game._magnet_mine_max_proximity_to_explode_meters = 50
        self.game._fps = 1
        self.game._magnet_mine_arming_time_seconds = 3
        self.game._magnet_mine_tracking_acceleration_ms = 10
        assert len(self.game._magnet_mines) == 0

        # ship 1 at 100, 100 meters
        self.game._ships[self.player_1_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_1_ship_id].coord_y = 100 * 10
        self.game._ships[self.player_1_ship_id].heading = 0
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 1
        # ship 2 500M north at 100, 600 meters
        self.game._ships[self.player_2_ship_id].coord_x = 100 * 10
        self.game._ships[self.player_2_ship_id].coord_y = 600 * 10

        self._game_frame = 4

        # Fire mine due north
        # moving at 100M/S, arming after 3 seconds.
        # mine will be 200 meters from ship 2
        # mine will be 300 meters from ship 1
        # mine should target ship 2
        self.game._ships[self.player_1_ship_id].cmd_launch_magnet_mine(
            launch_velocity=100
        )
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._magnet_mines) == 1
        mine_id = next(iter(self.game._magnet_mines.keys()))
        mine = self.game._magnet_mines[mine_id]
        assert mine.elapsed_milliseconds == 0
        assert not mine.armed
        assert mine.velocity_y_meters_per_second == 100
        self.game.advance_magnet_mines(fps=1)
        assert mine.elapsed_milliseconds == 1000
        assert not mine.armed
        assert mine.coord_x == 1000
        assert mine.coord_y == 2000
        assert mine.velocity_y_meters_per_second == 100
        self.game.advance_magnet_mines(fps=1)
        assert mine.elapsed_milliseconds == 2000
        assert not mine.armed
        assert mine.coord_x == 1000
        assert mine.coord_y == 3000
        assert mine.velocity_y_meters_per_second == 100
        self.game.advance_magnet_mines(fps=1)
        assert mine.elapsed_milliseconds == 3000
        assert not mine.armed
        assert mine.coord_y == 4000
        assert mine.velocity_y_meters_per_second == 100
        self.game.advance_magnet_mines(fps=1)
        assert mine.elapsed_milliseconds == 4000
        assert mine.armed
        assert mine.closest_ship_id == self.player_2_ship_id
        # close mine in, explode it on ship
        self.game.advance_magnet_mines(fps=3)
        assert not mine.exploded
        self.game.advance_magnet_mines(fps=3)
        assert not mine.exploded
        self.game.advance_magnet_mines(fps=3)
        assert not mine.exploded
        self.game._ships[self.player_2_ship_id].died_on_frame is None
        self.game.advance_magnet_mines(fps=10)
        assert mine.exploded
        self.game._ships[self.player_2_ship_id].died_on_frame is not None
