

from uuid import uuid4

from unittest import TestCase

from api.models.game import Game, GamePhase
from api.constants import HUNTER_DRONE_SLUG


class TestHunterDrone(TestCase):

    def pprint(self, *a):
        if self.show_debug:
            print(*a)

    def setUp(self):

        self.show_debug = False

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
        self.game._hunter_drone_arming_time_seconds = 4

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
                "meters_x": 10 * 1000, # 10KM
                "meters_y": 10 * 1000, # 10KM
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
        self.game._ships[self.player_1_ship_id].recoilless_tube_launches = True
        self.game._ships[self.player_2_ship_id].recoilless_tube_launches = True
        self.game._ships[self.player_1_ship_id].special_weapons_tubes_count = 1
        self.game._ships[self.player_2_ship_id].special_weapons_tubes_count = 1
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 2000
        self.game._ships[self.player_2_ship_id].virtual_ore_kg = 2000
        self.game._special_weapon_costs[HUNTER_DRONE_SLUG] = 500
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 0
        self.game._ships[self.player_2_ship_id].magnet_mines_loaded = 0
        self.game._ships[self.player_1_ship_id].emps_loaded = 0
        self.game._ships[self.player_2_ship_id].emps_loaded = 0
        self.game._ships[self.player_1_ship_id].hunter_drones_loaded = 0
        self.game._ships[self.player_2_ship_id].hunter_drones_loaded = 0

    def test_ship_can_buy_hunter_drone_if_tube_available(self):
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 0
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 2000
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 1
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 1500

    def test_ship_cannot_buy_hunter_drone_if_not_enough_ore(self):
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 0
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 400
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 0
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 400
        # double check
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 600
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 1

    def test_ship_cannot_buy_hunter_drone_if_not_enough_tubes(self):
        self.game._ships[self.player_1_ship_id].special_weapons_tubes_count = 1
        self.game._ships[self.player_1_ship_id].virtual_ore_kg = 1000
        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 1
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 0
        # double check
        self.game._ships[self.player_1_ship_id].special_weapons_tubes_count += 1
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 1

    def test_ship_cannot_buy_hunter_drone_if_not_docked_at_station(self):
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 0
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 2000
        self.game._ships[self.player_1_ship_id].docked_at_station = None
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 0
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 2000
        # Double check
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 1

    def test_ship_can_launch_a_hunter_drone(self):
        assert len(self.game._hunter_drones) == 0
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 0
        assert self.game._ships[self.player_1_ship_id].virtual_ore_kg == 2000
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        assert self.game._ships[self.player_1_ship_id].hunter_drones_loaded == 1
        # Fire drone
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))
        assert self.game._hunter_drones[hd_id].team_id == self.player_1_team_id
        assert self.game._hunter_drones[hd_id].ship_id == self.player_1_ship_id

    def test_drone_set_heading_method_updates_hitbox_values(self):
        self.game._ships[self.player_1_ship_id]._set_heading(90)
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        # Fire drone
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))

        # drone's heading matches the ship that launched it.
        assert self.game._hunter_drones[hd_id].heading == 90
        # check fixed hitbox coords
        assert self.game._hunter_drones[hd_id].rel_fixed_coord_hitbox_nose == (0, 15)
        assert self.game._hunter_drones[hd_id].rel_fixed_coord_hitbox_bottom_left == (-20, -15)
        assert self.game._hunter_drones[hd_id].rel_fixed_coord_hitbox_bottom_right == (20, -15)
        # check rotated hitbox coords
        assert self.game._hunter_drones[hd_id].rel_rot_coord_hitbox_nose == (15, 0)
        assert self.game._hunter_drones[hd_id].rel_rot_coord_hitbox_bottom_left == (-15, 20)
        assert self.game._hunter_drones[hd_id].rel_rot_coord_hitbox_bottom_right == (-15, -20)

        # adjust heading
        self.game._hunter_drones[hd_id].set_heading(180)
        assert self.game._hunter_drones[hd_id].heading == 180
        # check fixed hitbox coords are unchanged
        assert self.game._hunter_drones[hd_id].rel_fixed_coord_hitbox_nose == (0, 15)
        assert self.game._hunter_drones[hd_id].rel_fixed_coord_hitbox_bottom_left == (-20, -15)
        assert self.game._hunter_drones[hd_id].rel_fixed_coord_hitbox_bottom_right == (20, -15)
        # check rotated hitbox coords
        assert self.game._hunter_drones[hd_id].rel_rot_coord_hitbox_nose == (0, -15)
        assert self.game._hunter_drones[hd_id].rel_rot_coord_hitbox_bottom_left == (20, 15)
        assert self.game._hunter_drones[hd_id].rel_rot_coord_hitbox_bottom_right == (-20, 15)

    def test_a_launched_hunter_drone_has_constant_velocity(self):
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_1_ship_id]._set_heading(90)
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        # Fire drone
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))

        # drone sitting on ships nose
        assert self.game._hunter_drones[hd_id].coords == self.game._ships[self.player_1_ship_id].map_nose_coord
        # drone has ship velocity (0) + tube launch velocity
        assert self.game._hunter_drones[hd_id].velocity_x_meters_per_second == 10
        assert round(self.game._hunter_drones[hd_id].velocity_y_meters_per_second) == 0
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 0
        assert not self.game._hunter_drones[hd_id].armed

        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].velocity_x_meters_per_second == 10
        assert round(self.game._hunter_drones[hd_id].velocity_y_meters_per_second) == 0
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 1000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].coords[0] == self.game._ships[self.player_1_ship_id].map_nose_coord[0] + 10 * self.upm
        assert self.game._hunter_drones[hd_id].coords[1] == self.game._ships[self.player_1_ship_id].map_nose_coord[1]

        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].velocity_x_meters_per_second == 10
        assert round(self.game._hunter_drones[hd_id].velocity_y_meters_per_second) == 0
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 2000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].coords[0] == self.game._ships[self.player_1_ship_id].map_nose_coord[0] + 20 * self.upm
        assert self.game._hunter_drones[hd_id].coords[1] == self.game._ships[self.player_1_ship_id].map_nose_coord[1]

    def test_a_launched_hunter_drone_arms(self):
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_1_ship_id]._set_heading(90)
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        # Fire drone
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))

        # drone sitting on ships nose
        assert self.game._hunter_drones[hd_id].coords == self.game._ships[self.player_1_ship_id].map_nose_coord
        # drone has ship velocity (0) + tube launch velocity
        assert self.game._hunter_drones[hd_id].velocity_x_meters_per_second == 10
        assert round(self.game._hunter_drones[hd_id].velocity_y_meters_per_second) == 0
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 0
        assert not self.game._hunter_drones[hd_id].armed
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 1000
        assert not self.game._hunter_drones[hd_id].armed
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 2000
        assert not self.game._hunter_drones[hd_id].armed
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 3000
        assert not self.game._hunter_drones[hd_id].armed
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 4000
        assert not self.game._hunter_drones[hd_id].armed
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 5000
        assert self.game._hunter_drones[hd_id].armed # Drone armed

    def test_a_hunter_drone_flies_clockwise_patrol_if_no_targets_in_range(self):
        self.game._ships[self.player_1_ship_id].coord_x = 1000 * 10 # ship1 at 1000M, 10M
        self.game._ships[self.player_1_ship_id].coord_y = 10 * 10
        self.game._ships[self.player_1_ship_id]._hunter_drone_max_target_acquisition_distance_meters = 1000
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_2_ship_id].coord_x = 1000 * 10 # ship2 at 1000M, 6000M (out of range)
        self.game._ships[self.player_2_ship_id].coord_y = 6000 * 10

        # heading at 45 degrees, drone will fly clockwise patrol
        self.game._ships[self.player_1_ship_id]._set_heading(45)
        # Fire drone, heading locked at 45 until drone arms
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 1000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].heading == 45
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 2000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].heading == 45
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 3000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].heading == 45
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 4000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].heading == 45
        self.game.advance_hunter_drones(5)
        assert self.game._hunter_drones[hd_id].armed # Drone armed
        # heading increases as drone flies clockwise
        new_heading_1 = self.game._hunter_drones[hd_id].heading
        assert new_heading_1 > 45
        self.game.advance_hunter_drones(1)
        new_heading_2 = self.game._hunter_drones[hd_id].heading
        assert new_heading_2 > new_heading_1
        self.game.advance_hunter_drones(1)
        new_heading_3 = self.game._hunter_drones[hd_id].heading
        assert new_heading_3 > new_heading_2

    def test_a_hunter_drone_flies_counter_clockwise_patrol_if_no_targets_in_range(self):
        self.game._ships[self.player_1_ship_id].coord_x = 1000 * 10 # ship1 at 1000M, 10M
        self.game._ships[self.player_1_ship_id].coord_y = 10 * 10
        self.game._ships[self.player_1_ship_id]._hunter_drone_max_target_acquisition_distance_meters = 1000
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_2_ship_id].coord_x = 1000 * 10 # ship2 at 1000M, 6000M (out of range)
        self.game._ships[self.player_2_ship_id].coord_y = 6000 * 10

        # heading at 345 degrees, drone will fly counter clockwise patrol
        self.game._ships[self.player_1_ship_id]._set_heading(345)
        # Fire drone, heading locked at 45 until drone arms
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 1000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].heading == 345
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 2000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].heading == 345
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 3000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].heading == 345
        self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].elapsed_milliseconds == 4000
        assert not self.game._hunter_drones[hd_id].armed
        assert self.game._hunter_drones[hd_id].heading == 345
        self.game.advance_hunter_drones(5)
        assert self.game._hunter_drones[hd_id].armed # Drone armed
        # heading decreases as drone flies counter clockwise
        new_heading_1 = self.game._hunter_drones[hd_id].heading
        assert new_heading_1 < 345
        self.game.advance_hunter_drones(1)
        new_heading_2 = self.game._hunter_drones[hd_id].heading
        assert new_heading_2 < new_heading_1
        self.game.advance_hunter_drones(1)
        new_heading_3 = self.game._hunter_drones[hd_id].heading
        assert new_heading_3 < new_heading_2

    def test_a_hunter_drone_acquires_target_if_one_is_in_range(self):
        self.game._ships[self.player_1_ship_id].coord_x = 1000 * 10 # ship1 at 1000M, 10M
        self.game._ships[self.player_1_ship_id].coord_y = 10 * 10
        self.game._ships[self.player_1_ship_id]._hunter_drone_max_target_acquisition_distance_meters = 2000
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_2_ship_id].coord_x = 1000 * 10 # ship2 at 1000M, 1200M (in range)
        self.game._ships[self.player_2_ship_id].coord_y = 1200 * 10

        self.game._ships[self.player_1_ship_id]._set_heading(0)
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))
        while not self.game._hunter_drones[hd_id].armed:
            self.game.advance_hunter_drones(1)
        assert self.game._hunter_drones[hd_id].target_ship_id == self.player_2_ship_id

    def test_a_hunter_drone_flies_straight_trajectory_towards_a_target_and_kills_it(self):
        self.game._ships[self.player_1_ship_id].coord_x = 1000 * 10 # ship1 at 1000M, 10M
        self.game._ships[self.player_1_ship_id].coord_y = 10 * 10
        self.game._ships[self.player_1_ship_id]._hunter_drone_max_target_acquisition_distance_meters = 2000
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_2_ship_id].coord_x = 1000 * 10 # ship2 at 1000M, 1200M (in range)
        self.game._ships[self.player_2_ship_id].coord_y = 1200 * 10

        self.game._ships[self.player_1_ship_id]._set_heading(0)
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))
        iterations = 0
        while not self.game._hunter_drones[hd_id].exploded:
            iterations += 1
            if iterations > 200:
                raise AssertionError("too many iterations")
            self.game.advance_hunter_drones(1)
        assert self.game._ships[self.player_2_ship_id].died_on_frame is not None

    def test_a_hunter_drone_flies_curved_trajectory_towards_a_target_and_kills_it(self):
        self.game._ships[self.player_1_ship_id].coord_x = 1000 * 10 # ship1 at 1000M, 10M
        self.game._ships[self.player_1_ship_id].coord_y = 10 * 10
        self.game._ships[self.player_1_ship_id]._hunter_drone_max_target_acquisition_distance_meters = 2000
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_2_ship_id].coord_x = 1000 * 10 # ship2 at 1000M, 1200M (in range)
        self.game._ships[self.player_2_ship_id].coord_y = 1200 * 10

        self.game._ships[self.player_1_ship_id]._set_heading(60)
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))
        iterations = 0
        while not self.game._hunter_drones[hd_id].exploded:
            iterations += 1
            if iterations > 1000:
                raise AssertionError("too many iterations")
            self.game.advance_hunter_drones(15)
        assert self.game._ships[self.player_2_ship_id].died_on_frame is not None

    def test_a_hunter_drone_flies_retrograde_trajectory_towards_a_target_and_kills_it(self):
        self.game._ships[self.player_1_ship_id].coord_x = 1000 * 10 # ship1 at 1000M, 10M
        self.game._ships[self.player_1_ship_id].coord_y = 10 * 10
        self.game._ships[self.player_1_ship_id]._hunter_drone_max_target_acquisition_distance_meters = 2000
        self.game._ships[self.player_1_ship_id].docked_at_station = "foobar"
        self.game._ships[self.player_1_ship_id].cmd_buy_hunter_drone()
        self.game._ships[self.player_1_ship_id].velocity_x_meters_per_second = 0
        self.game._ships[self.player_1_ship_id].velocity_y_meters_per_second = 0
        self.game._ships[self.player_2_ship_id].coord_x = 1000 * 10 # ship2 at 1000M, 1200M (in range)
        self.game._ships[self.player_2_ship_id].coord_y = 1200 * 10

        # drone initially flying in opposite direction towards target.
        self.game._ships[self.player_1_ship_id]._set_heading(180)
        self.game._ships[self.player_1_ship_id].hunter_drone_launch_velocity = 10
        self.game._ships[self.player_1_ship_id].cmd_launch_hunter_drone()
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._hunter_drones) == 1
        hd_id = next(iter(self.game._hunter_drones.keys()))
        iterations = 0
        while not self.game._hunter_drones[hd_id].exploded:
            iterations += 1
            if iterations > 1000:
                raise AssertionError("too many iterations")
            self.game.advance_hunter_drones(15)
        assert self.game._ships[self.player_2_ship_id].died_on_frame is not None
