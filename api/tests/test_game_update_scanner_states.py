
from textwrap import indent
from uuid import uuid4
from unittest import TestCase

from api.models.game import Game, GamePhase, ShipScannerMode
from api import utils2d
from api.models.ship import VisibleElementShapeType

class TestGameUpdateScannerStatesForShips(TestCase):

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
        assert self.game._game_frame == 1
        for ship_id in self.game._ships:
            assert self.game._ships[ship_id].scanner_ship_data == {}

        self.game._ships[self.player_1_ship_id].visual_range = 1
        self.game._ships[self.player_2_ship_id].visual_range = 1


    def test_ship_1_and_ship_2_can_detect_eachother_with_radar(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = True

        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR

        self.game._ships[self.player_1_ship_id].scanner_radar_range = 1000 # 1000 meters
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 1000

        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 750, 750 meters
        self.game._ships[self.player_2_ship_id].coord_x = 750 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 750 * self.upm

        assert round(utils2d.calculate_point_distance(
            self.game._ships[self.player_1_ship_id].coords,
            self.game._ships[self.player_2_ship_id].coords,
        ) / self.upm) == 354
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)

        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1

        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['coord_x'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['coord_y'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['distance'] == 354
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['relative_heading'] == 45
        assert 'thermal_signature' not in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]

        assert self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]['coord_x'] == 500 * self.upm
        assert self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]['coord_y'] == 500 * self.upm
        assert self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]['distance'] == 354
        assert self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]['relative_heading'] == 225
        assert 'thermal_signature' not in self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]


    def test_ship_1_can_detect_ship_2_but_ship_2_cannot_detect_ship_1_when_scanner_offline(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = False

        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR

        self.game._ships[self.player_1_ship_id].scanner_radar_range = 1000 # 1000 meters
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 1000

        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 750, 750 meters
        self.game._ships[self.player_2_ship_id].coord_x = 750 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 750 * self.upm

        assert round(utils2d.calculate_point_distance(
            self.game._ships[self.player_1_ship_id].coords,
            self.game._ships[self.player_2_ship_id].coords,
        ) / self.upm) == 354
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)

        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0

        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['coord_x'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['coord_y'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['distance'] == 354
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['relative_heading'] == 45
        assert 'thermal_signature' not in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]


    def test_ships_cannot_detect_eachother_when_scanners_offline(self):
        self.game._ships[self.player_1_ship_id].scanner_online = False
        self.game._ships[self.player_2_ship_id].scanner_online = False

        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR

        self.game._ships[self.player_1_ship_id].scanner_radar_range = 1000 # 1000 meters
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 1000

        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 750, 750 meters
        self.game._ships[self.player_2_ship_id].coord_x = 750 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 750 * self.upm

        assert round(utils2d.calculate_point_distance(
            self.game._ships[self.player_1_ship_id].coords,
            self.game._ships[self.player_2_ship_id].coords,
        ) / self.upm) == 354
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0



    def test_ship_1_can_detect_ship_2_but_ship_2_cannot_detect_ship_1_when_ship_1_has_more_radar_range(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = True

        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR

        self.game._ships[self.player_1_ship_id].scanner_radar_range = 1000 # 1000 meters
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 200  # 200 meters (not enough range)

        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 750, 750 meters
        self.game._ships[self.player_2_ship_id].coord_x = 750 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 750 * self.upm

        assert round(utils2d.calculate_point_distance(
            self.game._ships[self.player_1_ship_id].coords,
            self.game._ships[self.player_2_ship_id].coords,
        ) / self.upm) == 354
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)

        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0

        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['coord_x'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['coord_y'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['distance'] == 354
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['relative_heading'] == 45
        assert 'thermal_signature' not in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]

        # Flip Ranges
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 1000 # 1000 meters
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 200  # 200 meters (not enough range)
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        # Now ship 2 can see ship 1, but ship 1 cannot see ship 2.
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1


    def test_ship_1_cant_detect_ship_2_with_radar_but_cannot_detect_with_ir(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = True

        self.game._ships[self.player_1_ship_id].scanner_radar_range = 1000 # 1000 meters
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 1000
        self.game._ships[self.player_1_ship_id].scanner_ir_range = 2000    # 2000 meters
        self.game._ships[self.player_2_ship_id].scanner_ir_range = 2000

        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR

        self.game._ships[self.player_1_ship_id].scanner_ir_minimum_thermal_signature = 50
        self.game._ships[self.player_2_ship_id].scanner_ir_minimum_thermal_signature = 50
        self.game._ships[self.player_1_ship_id].scanner_thermal_signature = 75
        self.game._ships[self.player_2_ship_id].scanner_thermal_signature = 75


        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1600, 1600 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1600 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1600 * self.upm

        assert round(utils2d.calculate_point_distance(
            self.game._ships[self.player_1_ship_id].coords,
            self.game._ships[self.player_2_ship_id].coords,
        ) / self.upm) == 1556 # meters

        # Ship 1 cannot find ship 2 with RADAR scanner (too far away)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0

        # Ship 1 can find ship 2 with INFRA RED scanner (ship is close enough with high enough of a thermal signature)
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.IR
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['scanner_thermal_signature'] == 75
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['coord_x'] == 1600 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['coord_y'] == 1600 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['distance'] == 1556
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['relative_heading'] == 45


    def test_ship_1_cant_detect_ship_2_with_radar_beacuse_out_of_range_and_cannot_detect_with_ir_because_ship_2_thermal_signature_too_low(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = False

        self.game._ships[self.player_1_ship_id].scanner_radar_range = 1000 # 1000 meters
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 1000
        self.game._ships[self.player_1_ship_id].scanner_ir_range = 2000    # 2000 meters
        self.game._ships[self.player_2_ship_id].scanner_ir_range = 2000

        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR

        self.game._ships[self.player_1_ship_id].scanner_ir_minimum_thermal_signature = 80
        self.game._ships[self.player_2_ship_id].scanner_thermal_signature = 75

        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1600, 1600 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1600 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1600 * self.upm

        assert round(utils2d.calculate_point_distance(
            self.game._ships[self.player_1_ship_id].coords,
            self.game._ships[self.player_2_ship_id].coords,
        ) / self.upm) == 1556 # meters

        # Ship 1 cannot find ship 2 with RADAR scanner (too far away)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0

        # Ship 1 cannot find ship 2 with IR because heat signature too low
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.IR
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0

        # Boost thermal signature of ship 2 and it can be detected
        self.game._ships[self.player_2_ship_id].scanner_thermal_signature = 100
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0
        assert self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]['scanner_thermal_signature'] == 100


    def test_ship1_and_ship2_can_see_eachother_within_visual_range_scanners_offline(self):
        self.game._ships[self.player_1_ship_id].scanner_online = False
        self.game._ships[self.player_2_ship_id].scanner_online = False
        self.game._ships[self.player_1_ship_id].visual_range = 1000
        self.game._ships[self.player_2_ship_id].visual_range = 1000
        self.game._ships[self.player_1_ship_id].engine_lit = False
        self.game._ships[self.player_2_ship_id].engine_lit = True

        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1000, 1000 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1000 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1000 * self.upm

        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0

        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1
        self.assertEqual(self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id],
            {
                'id': self.player_2_ship_id,
                'designator': self.game._ships[self.player_2_ship_id].scanner_designator,
                'coord_x': 1000 * self.upm,
                'coord_y': 1000 * self.upm,
                'in_visual_range': True,
                'visual_shape': VisibleElementShapeType.RECT,
                'velocity_y_meters_per_second': 0,
                'velocity_x_meters_per_second': 0,
                'visual_p0': self.game._ships[self.player_2_ship_id].map_p0,
                'visual_p1': self.game._ships[self.player_2_ship_id].map_p1,
                'visual_p2': self.game._ships[self.player_2_ship_id].map_p2,
                'visual_p3': self.game._ships[self.player_2_ship_id].map_p3,
                'visual_engine_lit': True,
                'visual_engine_boosted_last_frame':-10,
                'visual_ebeam_charging': False,
                'visual_ebeam_firing': False,
                'visual_ebeam_color': '#ff0000',
                'visual_fill_color': '#ffffff',
                'visual_fin_0_rel_rot_coord_0': (9980, 9970),
                'visual_fin_0_rel_rot_coord_1': (9952, 9940),
                'visual_fin_1_rel_rot_coord_0': (10020, 9970),
                'visual_fin_1_rel_rot_coord_1': (10048, 9940),
                'visual_gravity_brake_position': 0,
                'visual_gravity_brake_deployed_position': 100,
                'visual_gravity_brake_active': False,
                'visual_mining_ore_location': None,
                'visual_fueling_at_station': False,
                'aflame': False,
                'exploded': False,
                'alive': True,
                'target_heading': 45,
                "relative_heading": 45,
                "distance": 707,
                'anti_radar_coating_level':0,
                'scanner_thermal_signature': 0,
            }
        )
        self.assertEqual(self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id],
            {
                'id': self.player_1_ship_id,
                'designator': self.game._ships[self.player_1_ship_id].scanner_designator,
                'coord_x': 500 * self.upm,
                'coord_y': 500 * self.upm,
                'visual_shape': VisibleElementShapeType.RECT,
                'in_visual_range': True,
                'visual_p0': self.game._ships[self.player_1_ship_id].map_p0,
                'visual_p1': self.game._ships[self.player_1_ship_id].map_p1,
                'visual_p2': self.game._ships[self.player_1_ship_id].map_p2,
                'visual_p3': self.game._ships[self.player_1_ship_id].map_p3,
                'velocity_y_meters_per_second': 0,
                'velocity_x_meters_per_second': 0,
                'visual_engine_lit': False,
                'visual_engine_boosted_last_frame':-10,
                'visual_ebeam_charging': False,
                'visual_ebeam_firing': False,
                'visual_ebeam_color': '#ff0000',
                'visual_fill_color': '#ffffff',
                'visual_fin_0_rel_rot_coord_0': (4980, 4970),
                'visual_fin_0_rel_rot_coord_1': (4952, 4940),
                'visual_fin_1_rel_rot_coord_0': (5020, 4970),
                'visual_fin_1_rel_rot_coord_1': (5048, 4940),
                'visual_gravity_brake_position': 0,
                'visual_gravity_brake_deployed_position': 100,
                'visual_gravity_brake_active': False,
                'visual_fueling_at_station': False,
                'visual_mining_ore_location': None,
                'aflame': False,
                'exploded': False,
                'alive': True,
                'target_heading': 225,
                "relative_heading": 225,
                "distance": 707,
                'anti_radar_coating_level':0,
                'scanner_thermal_signature': 0,
            }
        )

    def test_ship2_can_see_ship1_if_ship2_has_enough_visual_range_and_ship1_does_not(self):
        self.game._ships[self.player_1_ship_id].scanner_online = False
        self.game._ships[self.player_2_ship_id].scanner_online = False
        self.game._ships[self.player_1_ship_id].visual_range = 250
        self.game._ships[self.player_2_ship_id].visual_range = 1000

        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1000, 1000 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1000 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1000 * self.upm

        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0

        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1
        self.assertEqual(self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id], {
            'id': self.player_1_ship_id,
            'designator': self.game._ships[self.player_1_ship_id].scanner_designator,
            'coord_x': 500 * self.upm,
            'coord_y': 500 * self.upm,
            'in_visual_range': True,
            'visual_shape': VisibleElementShapeType.RECT,
            'visual_p0': self.game._ships[self.player_1_ship_id].map_p0,
            'visual_p1': self.game._ships[self.player_1_ship_id].map_p1,
            'visual_p2': self.game._ships[self.player_1_ship_id].map_p2,
            'visual_p3': self.game._ships[self.player_1_ship_id].map_p3,
            'visual_engine_lit': False,
            'velocity_x_meters_per_second': 0,
            'velocity_y_meters_per_second': 0,
            'visual_engine_boosted_last_frame': -10,
            'visual_ebeam_charging': False,
            'visual_ebeam_firing': False,
            'visual_ebeam_color': '#ff0000',
            'visual_fill_color': '#ffffff',
            'visual_fin_0_rel_rot_coord_0': (4980, 4970),
            'visual_fin_0_rel_rot_coord_1': (4952, 4940),
            'visual_fin_1_rel_rot_coord_0': (5020, 4970),
            'visual_fin_1_rel_rot_coord_1': (5048, 4940),
            'visual_gravity_brake_position': 0,
            'visual_gravity_brake_deployed_position': 100,
            'visual_gravity_brake_active': False,
            'visual_fueling_at_station': False,
            'visual_mining_ore_location': None,
            'aflame': False,
            'exploded': False,
            'alive': True,
            "distance": 707,
            "relative_heading": 225,
            "target_heading": 225.0,
            'anti_radar_coating_level':0,
            'scanner_thermal_signature': 0,
        })

    def test_ship_1_and_ship_2_can_spot_eachother_with_radar_scanner_only(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_1_ship_id].scanner_radar_sensitivity = 0
        self.game._ships[self.player_2_ship_id].scanner_radar_sensitivity = 0
        self.game._ships[self.player_1_ship_id].anti_radar_coating_level = 0
        self.game._ships[self.player_2_ship_id].anti_radar_coating_level = 0
        self.game._ships[self.player_1_ship_id].visual_range = 1000
        self.game._ships[self.player_2_ship_id].visual_range = 1000
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 2000

        # Place ships outside of visual range, but withing radar range (both)
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm

        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1

        # scanner data is loaded
        assert 'relative_heading' in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]
        assert 'relative_heading' in self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]


    def test_ship_1_can_spot_ship_2_radar_scanner_only_and_Ship_2_cannot_spot_ship_1_due_to_anti_radar_coating(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_1_ship_id].scanner_radar_sensitivity = 0
        self.game._ships[self.player_2_ship_id].scanner_radar_sensitivity = 0
        self.game._ships[self.player_1_ship_id].anti_radar_coating_level = 1
        self.game._ships[self.player_2_ship_id].anti_radar_coating_level = 0
        self.game._ships[self.player_1_ship_id].visual_range = 1000
        self.game._ships[self.player_2_ship_id].visual_range = 1000
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 2000

        # Place ships outside of visual range, but withing radar range (both)
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm

        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert 'relative_heading' in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0 # Ship 2 radar sensitivity too low

        self.game._ships[self.player_2_ship_id].scanner_radar_sensitivity = 1
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1 # ship 2 can now spot
        assert 'relative_heading' in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]
        assert 'relative_heading' in self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]


    def test_ships_can_visual_spot_each_other_if_one_ship_has_higher_anti_radar_value(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_1_ship_id].scanner_radar_sensitivity = 0
        self.game._ships[self.player_2_ship_id].scanner_radar_sensitivity = 0
        self.game._ships[self.player_1_ship_id].anti_radar_coating_level = 1
        self.game._ships[self.player_2_ship_id].anti_radar_coating_level = 0
        self.game._ships[self.player_1_ship_id].visual_range = 2000
        self.game._ships[self.player_2_ship_id].visual_range = 2000
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 2000

        # Place ships inside both visual range and radar range
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm

        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1
        assert 'relative_heading' in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]
        assert 'relative_heading' in self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]

        self.game._ships[self.player_2_ship_id].scanner_radar_sensitivity = 1
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1
        assert 'relative_heading' in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]
        assert 'relative_heading' in self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]


    def test_ship_channeling_scanner_lock_is_interrupted_if_target_goes_outside_of_scanner_range(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR

        # Ship 1 locking onto ship 2
        self.game._ships[self.player_1_ship_id].scanner_locking = True
        self.game._ships[self.player_1_ship_id].scanner_lock_target = self.player_2_ship_id
        self.game._ships[self.player_1_ship_id].scanner_locking_power_used = 0
        self.game._ships[self.player_1_ship_id].scanner_get_lock_power_requirement_per_second = 1000
        self.game._ships[self.player_1_ship_id].scanner_get_lock_power_requirement_total = 2000

        # Place ships inside radar range
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm

        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1
        assert not self.game._ships[self.player_1_ship_id].scanner_locked
        assert self.game._ships[self.player_1_ship_id].scanner_locking
        assert self.game._ships[self.player_1_ship_id].scanner_lock_target == self.player_2_ship_id
        assert self.game._ships[self.player_1_ship_id].scanner_locking_power_used == 0

        # Move ship 2 outside radar range and assert locking is cancelled
        # Ship 2 at 2500, 2500 meters
        self.game._ships[self.player_2_ship_id].coord_x = 2500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 2500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0
        assert not self.game._ships[self.player_1_ship_id].scanner_locked
        assert not self.game._ships[self.player_1_ship_id].scanner_locking
        assert self.game._ships[self.player_1_ship_id].scanner_lock_target is None
        assert self.game._ships[self.player_1_ship_id].scanner_locking_power_used is None


    def test_ship_scanner_lock_is_lost_if_target_goes_outside_of_scanner_range(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR

        # Ship 1 locked onto ship 2
        self.game._ships[self.player_1_ship_id].scanner_locking = False
        self.game._ships[self.player_1_ship_id].scanner_locked = True
        self.game._ships[self.player_1_ship_id].scanner_lock_target = self.player_2_ship_id
        self.game._ships[self.player_1_ship_id].scanner_locking_power_used = None

        # Place ships inside radar range
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm

        # Ship 1 is locked onto ship 2
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 1
        assert self.game._ships[self.player_1_ship_id].scanner_locked
        assert self.game._ships[self.player_1_ship_id].scanner_lock_target == self.player_2_ship_id

        # Move ship 2 outside radar range and assert lock is lost
        # Ship 2 at 2500, 2500 meters
        self.game._ships[self.player_2_ship_id].coord_x = 2500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 2500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_ship_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_ship_data) == 0
        assert not self.game._ships[self.player_1_ship_id].scanner_locked
        assert self.game._ships[self.player_1_ship_id].scanner_lock_target is None


    def test_scanner_ship_data_includes_exact_heading_when_scanner_is_online(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_2_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_2_ship_id].scanner_mode = ShipScannerMode.RADAR

        # Place ships inside radar range
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm

        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)

        assert "relative_heading" in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]
        assert "target_heading" in self.game._ships[self.player_1_ship_id].scanner_ship_data[self.player_2_ship_id]
        assert "relative_heading" in self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]
        assert "target_heading" in self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]

        assert isinstance(self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]['target_heading'], float)
        assert isinstance(self.game._ships[self.player_2_ship_id].scanner_ship_data[self.player_1_ship_id]['relative_heading'], int)


    # Test Scanner Lock/Locking Traversal Limits
    def test_locking_scanner_sets_ships_previous_traversal_degrees(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_1_ship_id].scanner_locking = True
        self.game._ships[self.player_1_ship_id].scanner_lock_target = self.player_2_ship_id
        self.game._ships[self.player_1_ship_id].scanner_idle_power_requirement_per_second = 1
        self.game._ships[self.player_1_ship_id].battery_power = 500_000
        # Place ships inside radar range
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters (45.0 degrees)
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        assert round(self.game._ships[self.player_1_ship_id].scanner_lock_traversal_degrees_previous_frame) == 45

    def test_scanner_maintains_locking_channel_when_traversal_degrees_are_below_locking_max(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_1_ship_id].scanner_locking = True
        self.game._ships[self.player_1_ship_id].scanner_lock_target = self.player_2_ship_id
        self.game._ships[self.player_1_ship_id].scanner_idle_power_requirement_per_second = 1
        self.game._ships[self.player_1_ship_id].battery_power = 500_000
        self.game._ships[self.player_1_ship_id].scanner_locking_max_traversal_degrees = 5
        self.game._fps = 2
        # Place ships inside radar range
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters (45.0 degrees)
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        assert round(self.game._ships[self.player_1_ship_id].scanner_lock_traversal_degrees_previous_frame) == 45

        # Adjust ship 2's position so it's bearing is slightly more than 45 degrees
        self.game._ships[self.player_2_ship_id].coord_x = 1550 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].scanner_locking is True
        assert self.game._ships[self.player_1_ship_id].scanner_lock_traversal_degrees_previous_frame > 45
        assert self.game._ships[self.player_1_ship_id].scanner_lock_traversal_slack < 1

    def test_scanner_loses_locking_channel_when_traversal_degrees_are_abovw_locking_max(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_1_ship_id].scanner_locking = True
        self.game._ships[self.player_1_ship_id].scanner_lock_target = self.player_2_ship_id
        self.game._ships[self.player_1_ship_id].scanner_idle_power_requirement_per_second = 1
        self.game._ships[self.player_1_ship_id].battery_power = 500_000
        self.game._ships[self.player_1_ship_id].scanner_locking_max_traversal_degrees = 1
        self.game._fps = 2
        # Place ships inside radar range
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters (45.0 degrees)
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        assert round(self.game._ships[self.player_1_ship_id].scanner_lock_traversal_degrees_previous_frame) == 45
        assert self.game._ships[self.player_1_ship_id].scanner_locking is True

        # Adjust ship 2's position so it's bearing is slightly more than 45 degrees (above max)
        self.game._ships[self.player_2_ship_id].coord_x = 1550 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].scanner_locking is False
        assert self.game._ships[self.player_1_ship_id].scanner_lock_traversal_degrees_previous_frame is None
        assert self.game._ships[self.player_1_ship_id].scanner_lock_traversal_slack is None

    def test_scanner_maintains_lock_when_traversal_degrees_are_below_lock_max(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_1_ship_id].scanner_locking = False
        self.game._ships[self.player_1_ship_id].scanner_locked = True
        self.game._ships[self.player_1_ship_id].scanner_lock_target = self.player_2_ship_id
        self.game._ships[self.player_1_ship_id].scanner_idle_power_requirement_per_second = 1
        self.game._ships[self.player_1_ship_id].battery_power = 500_000
        self.game._ships[self.player_1_ship_id].scanner_locked_max_traversal_degrees = 5
        self.game._fps = 2
        # Place ships inside radar range
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters (45.0 degrees)
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        assert round(self.game._ships[self.player_1_ship_id].scanner_lock_traversal_degrees_previous_frame) == 45

        # Adjust ship 2's position so it's bearing is slightly more than 45 degrees
        self.game._ships[self.player_2_ship_id].coord_x = 1550 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].scanner_locked is True
        assert self.game._ships[self.player_1_ship_id].scanner_lock_traversal_degrees_previous_frame > 45
        assert self.game._ships[self.player_1_ship_id].scanner_lock_traversal_slack < 1


    def test_scanner_loses_lock_when_traversal_degrees_are_above_lock_max(self):
        self.game._ships[self.player_1_ship_id].scanner_online = True
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 2000
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.RADAR
        self.game._ships[self.player_1_ship_id].scanner_locking = False
        self.game._ships[self.player_1_ship_id].scanner_locked = True
        self.game._ships[self.player_1_ship_id].scanner_lock_target = self.player_2_ship_id
        self.game._ships[self.player_1_ship_id].scanner_idle_power_requirement_per_second = 1
        self.game._ships[self.player_1_ship_id].battery_power = 500_000
        self.game._ships[self.player_1_ship_id].scanner_locked_max_traversal_degrees = 1
        self.game._fps = 2
        # Place ships inside radar range
        # Ship 1 at 500, 500 meters
        self.game._ships[self.player_1_ship_id].coord_x = 500 * self.upm
        self.game._ships[self.player_1_ship_id].coord_y = 500 * self.upm
        # Ship 2 at 1500, 1500 meters (45.0 degrees)
        self.game._ships[self.player_2_ship_id].coord_x = 1500 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        assert round(self.game._ships[self.player_1_ship_id].scanner_lock_traversal_degrees_previous_frame) == 45
        assert self.game._ships[self.player_1_ship_id].scanner_locked is True

        # Adjust ship 2's position so it's bearing is slightly more than 45 degrees
        self.game._ships[self.player_2_ship_id].coord_x = 1550 * self.upm
        self.game._ships[self.player_2_ship_id].coord_y = 1500 * self.upm
        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        assert self.game._ships[self.player_1_ship_id].scanner_locked is False
        assert self.game._ships[self.player_1_ship_id].scanner_lock_traversal_degrees_previous_frame is None
        assert self.game._ships[self.player_1_ship_id].scanner_lock_traversal_slack is None


class TestGameUpdateScannerStatesForMines(TestCase):

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
        assert self.game._game_frame == 1
        for ship_id in self.game._ships:
            assert self.game._ships[ship_id].scanner_ship_data == {}

        self.game._ships[self.player_1_ship_id].visual_range = 1
        self.game._ships[self.player_2_ship_id].visual_range = 1

        self.game._ships[self.player_1_ship_id].magnet_mines_loaded = 5
        self.game._ships[self.player_2_ship_id].magnet_mines_loaded = 5


    def test_both_ships_can_visually_spot_mine_if_mine_in_visual_range_for_both(self):
        self.game._ships[self.player_1_ship_id].visual_range = 1000
        self.game._ships[self.player_2_ship_id].visual_range = 1000

        assert len(self.game._ships[self.player_1_ship_id].scanner_magnet_mine_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_magnet_mine_data) == 0

        self.game._ships[self.player_1_ship_id].cmd_launch_magnet_mine(
            launch_velocity=10
        )
        self.game.calculate_weapons_and_damage(self.player_1_ship_id)
        assert len(self.game._magnet_mines) == 1

        self.game.reset_and_update_scanner_states(self.player_1_ship_id)
        self.game.reset_and_update_scanner_states(self.player_2_ship_id)
        assert len(self.game._ships[self.player_1_ship_id].scanner_magnet_mine_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_magnet_mine_data) == 1
