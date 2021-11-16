
from uuid import uuid4
from unittest import TestCase

from api.models.game import Game, GamePhase, ShipScannerMode
from api import utils2d


class TestGameUpdateScannerStates(TestCase):

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

        self.game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 100 * 1000 * self.upm, # 100 KM
            'y_unit_length': 100 * 1000 * self.upm, # 100 KM
        })
        assert self.game.map_is_configured
        self.game.advance_to_phase_1_starting()

        self.player_1_ship_id = self.game._player_id_to_ship_id_map[self.player_1_id]
        self.player_2_ship_id = self.game._player_id_to_ship_id_map[self.player_2_id]

        self.game._game_start_countdown = 1
        self.game.decr_phase_1_starting_countdown()
        assert self.game._phase == GamePhase.LIVE
        assert self.game._game_frame == 1
        for ship_id in self.game._ships:
            assert self.game._ships[ship_id].scanner_data == {}


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
        self.game.update_scanner_states()

        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 1

        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['coord_x'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['coord_y'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['distance'] == 354
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['relative_heading'] == 45
        assert 'diameter_meters' in self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]
        assert 'thermal_signature' not in self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]

        assert self.game._ships[self.player_2_ship_id].scanner_data[self.player_1_ship_id]['coord_x'] == 500 * self.upm
        assert self.game._ships[self.player_2_ship_id].scanner_data[self.player_1_ship_id]['coord_y'] == 500 * self.upm
        assert self.game._ships[self.player_2_ship_id].scanner_data[self.player_1_ship_id]['distance'] == 354
        assert self.game._ships[self.player_2_ship_id].scanner_data[self.player_1_ship_id]['relative_heading'] == 225
        assert 'diameter_meters' in self.game._ships[self.player_2_ship_id].scanner_data[self.player_1_ship_id]
        assert 'thermal_signature' not in self.game._ships[self.player_2_ship_id].scanner_data[self.player_1_ship_id]


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
        self.game.update_scanner_states()

        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0

        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['coord_x'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['coord_y'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['distance'] == 354
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['relative_heading'] == 45
        assert 'diameter_meters' in self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]
        assert 'thermal_signature' not in self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]


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
        self.game.update_scanner_states()
        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0



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
        self.game.update_scanner_states()

        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0

        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['coord_x'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['coord_y'] == 750 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['distance'] == 354
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['relative_heading'] == 45
        assert 'diameter_meters' in self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]
        assert 'thermal_signature' not in self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]

        # Flip Ranges
        self.game._ships[self.player_2_ship_id].scanner_radar_range = 1000 # 1000 meters
        self.game._ships[self.player_1_ship_id].scanner_radar_range = 200  # 200 meters (not enough range)
        self.game.update_scanner_states()
        # Now ship 2 can see ship 1, but ship 1 cannot see ship 2.
        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 1


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
        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0
        self.game.update_scanner_states()
        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0

        # Ship 1 can find ship 2 with INFRA RED scanner (ship is close enough with high enough of a thermal signature)
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.IR
        self.game.update_scanner_states()
        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['thermal_signature'] == 75
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['coord_x'] == 1600 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['coord_y'] == 1600 * self.upm
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['distance'] == 1556
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['relative_heading'] == 45


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
        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0
        self.game.update_scanner_states()
        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0

        # Ship 1 cannot find ship 2 with IR because heat signature too low
        self.game._ships[self.player_1_ship_id].scanner_mode = ShipScannerMode.IR
        self.game.update_scanner_states()
        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 0
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0

        # Boost thermal signature of ship 2 and it can be detected
        self.game._ships[self.player_2_ship_id].scanner_thermal_signature = 100
        self.game.update_scanner_states()
        assert len(self.game._ships[self.player_1_ship_id].scanner_data) == 1
        assert len(self.game._ships[self.player_2_ship_id].scanner_data) == 0
        assert self.game._ships[self.player_1_ship_id].scanner_data[self.player_2_ship_id]['thermal_signature'] == 100
