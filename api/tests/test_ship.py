
from unittest import TestCase

from api.models.ship import Ship, ShipStateKey
from api import constants



class TestShipAdjustResources(TestCase):
    def setUp(self):
        self.ship = Ship.spawn(map_units_per_meter=10)
        self.ship.reaction_wheel_online = False

    def test_battery_power_reduced_if_reaction_wheel_online(self):
        ''' REACTION WHEEL '''
        self.ship.reaction_wheel_online = True
        start_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_power - constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME
        assert self.ship.reaction_wheel_online

    def test_battery_power_not_reduced_if_reaction_wheel_offline(self):
        ''' REACTION WHEEL '''
        self.ship.reaction_wheel_online = False
        start_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_power
        assert not self.ship.reaction_wheel_online

    def test_reaction_wheel_disabled_if_battery_runs_out_of_power(self):
        ''' REACTION WHEEL '''
        self.ship.reaction_wheel_online = True

        # Enough power to run the reaction wheel for 3 frames
        self.ship.battery_power = constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 3

        self.ship.adjust_resources()
        assert self.ship.battery_power == constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 2
        assert self.ship.reaction_wheel_online

        self.ship.adjust_resources()
        assert self.ship.battery_power == constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 1
        assert self.ship.reaction_wheel_online

        self.ship.adjust_resources()
        assert self.ship.battery_power == constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 0
        assert self.ship.reaction_wheel_online

        self.ship.adjust_resources() # No battery power to run reaction wheel.
        assert self.ship.battery_power == constants.REACTION_WHEEL_POWER_REQUIREMENT_PER_FRAME * 0
        assert not self.ship.reaction_wheel_online # Reaction wheel disabled.


    def test_engine_start_process_uses_power(self):
        ''' ENGINE ACTIVATE '''
        self.ship.game_frame = 1
        self.ship._state[ShipStateKey.ENGINE] = {
            'starting': True,
            'last_frame': 3,
        }
        start_battery_power = self.ship.battery_power
        power_usage_per_frame_eng_start = self.ship.engine_activation_power_required_per_frame

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 1
        assert not self.ship.engine_online
        assert ShipStateKey.ENGINE in self.ship._state

        self.ship.game_frame = 2
        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 2
        assert not self.ship.engine_online
        assert ShipStateKey.ENGINE in self.ship._state

        self.ship.game_frame = 3
        self.ship.adjust_resources()
        assert self.ship.battery_power == (
            start_battery_power - (
                power_usage_per_frame_eng_start * 2
                + self.ship.engine_idle_power_requirement_per_frame
            )
        )
        assert self.ship.engine_online
        assert not self.ship.engine_lit
        assert ShipStateKey.ENGINE not in self.ship._state

    def test_engine_start_process_fails_if_not_enough_power(self):
        ''' ENGINE ACTIVATE '''
        self.ship.game_frame = 1
        self.ship._state[ShipStateKey.ENGINE] = {
            'starting': True,
            'last_frame': 3,
        }
        start_battery_power = self.ship.battery_power
        power_usage_per_frame_eng_start = self.ship.engine_activation_power_required_per_frame

        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 1
        assert not self.ship.engine_online
        assert ShipStateKey.ENGINE in self.ship._state

        self.ship.game_frame = 2
        self.ship.adjust_resources()
        assert self.ship.battery_power == start_battery_power - power_usage_per_frame_eng_start * 2
        assert not self.ship.engine_online
        assert ShipStateKey.ENGINE in self.ship._state

        self.ship.game_frame = 3
        self.ship.battery_power = 0
        self.ship.adjust_resources()
        assert not self.ship.engine_online
        assert not self.ship.engine_lit
        assert ShipStateKey.ENGINE not in self.ship._state

    def test_idle_engine_uses_power(self):
        ''' ENGINE IDLE '''
        self.ship.engine_online = True
        starting_fuel = self.ship.fuel_level
        starting_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.battery_power == starting_power - self.ship.engine_idle_power_requirement_per_frame * 1
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

        self.ship.adjust_resources()
        assert self.ship.battery_power == starting_power - self.ship.engine_idle_power_requirement_per_frame * 2
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

    def test_idle_engine_deactivates_if_not_enough_power(self):
        ''' ENGINE IDLE '''
        self.ship.engine_online = True
        starting_fuel = self.ship.fuel_level
        starting_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.battery_power == starting_power - self.ship.engine_idle_power_requirement_per_frame * 1
        assert self.ship.fuel_level == starting_fuel
        assert self.ship.engine_online

        # Not enough power to idle the engine for another frame
        self.ship.battery_power = self.ship.engine_idle_power_requirement_per_frame - 1
        self.ship.adjust_resources()
        assert self.ship.battery_power == (self.ship.engine_idle_power_requirement_per_frame - 1)
        assert self.ship.fuel_level == starting_fuel
        assert not self.ship.engine_online

    def test_lit_engine_uses_fuel_and_generates_power(self):
        ''' ENGINE LIT '''
        self.ship.engine_online = True
        self.ship.engine_lit = True
        start_fuel = self.ship.fuel_level
        start_power = self.ship.battery_power
        fuel_usage_per_frame = self.ship.engine_fuel_usage_per_frame
        power_gen_per_frame = self.ship.engine_battery_charge_per_frame

        self.ship.adjust_resources()
        assert self.ship.fuel_level == start_fuel - fuel_usage_per_frame * 1
        assert self.ship.battery_power == start_power + power_gen_per_frame * 1
        assert self.ship.engine_online
        assert self.ship.engine_lit

        self.ship.adjust_resources()
        assert self.ship.fuel_level == start_fuel - fuel_usage_per_frame * 2
        assert self.ship.battery_power == start_power + power_gen_per_frame * 2
        assert self.ship.engine_online
        assert self.ship.engine_lit

    def test_lit_engine_flames_out_if_not_enough_fuel(self):
        ''' ENGINE LIT '''
        self.ship.engine_online = True
        self.ship.engine_lit = True
        fuel_usage_per_frame = self.ship.engine_fuel_usage_per_frame
        power_gen_per_frame = self.ship.engine_battery_charge_per_frame

        # Enough fuel for exactly 1 frame
        self.ship.fuel_level = round(fuel_usage_per_frame * 1.5)
        start_fuel = self.ship.fuel_level
        start_power = self.ship.battery_power

        self.ship.adjust_resources()
        assert self.ship.fuel_level == start_fuel - fuel_usage_per_frame * 1
        assert self.ship.battery_power == start_power + power_gen_per_frame * 1
        assert self.ship.engine_online
        assert self.ship.engine_lit

        # Flame out
        self.ship.adjust_resources()
        assert self.ship.fuel_level == start_fuel - fuel_usage_per_frame * 1
        assert self.ship.battery_power == start_power + power_gen_per_frame * 1
        assert not self.ship.engine_online
        assert not self.ship.engine_lit


class TestShipCMDSetHeading(TestCase):

    def setUp(self):
        self.ship = Ship.spawn(map_units_per_meter=10)
        self.ship.reaction_wheel_online = True

    def _assert_ship_heading_0(self):
        assert self.ship.heading == 0
        assert self.ship.rel_rot_coord_0 == (-20, -60)
        assert self.ship.rel_rot_coord_1 == (-20, 60)
        assert self.ship.rel_rot_coord_2 == (20, 60)
        assert self.ship.rel_rot_coord_3 == (20, -60)
        assert self.ship.rel_rot_coord_0 == self.ship.heading_0_rel_coord_0
        assert self.ship.rel_rot_coord_1 == self.ship.heading_0_rel_coord_1
        assert self.ship.rel_rot_coord_2 == self.ship.heading_0_rel_coord_2
        assert self.ship.rel_rot_coord_3 == self.ship.heading_0_rel_coord_3

    def _assert_heading_0_cords_fixed(self):
        assert self.ship.heading_0_rel_coord_0 == (-20, -60)
        assert self.ship.heading_0_rel_coord_1 == (-20, 60)
        assert self.ship.heading_0_rel_coord_2 == (20, 60)
        assert self.ship.heading_0_rel_coord_3 == (20, -60)

    def test_ship_cannot_rotate_if_reaction_wheel_is_offline(self):
        self._assert_ship_heading_0()
        self.ship.reaction_wheel_online = False
        self.ship.cmd_set_heading(30)
        self._assert_ship_heading_0()

    def test_rotate_ship_to_0_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(0)
        self._assert_ship_heading_0()
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_90_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(90)
        assert self.ship.heading == 90
        assert self.ship.rel_rot_coord_0 == (-60, 20,)
        assert self.ship.rel_rot_coord_1 == (60, 20,)
        assert self.ship.rel_rot_coord_2 ==  (60, -20,)
        assert self.ship.rel_rot_coord_3 == (-60, -20,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_180_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(180)
        assert self.ship.heading == 180
        assert self.ship.rel_rot_coord_0 == (20, 60,)
        assert self.ship.rel_rot_coord_1 == (20, -60,)
        assert self.ship.rel_rot_coord_2 ==  (-20, -60,)
        assert self.ship.rel_rot_coord_3 == (-20, 60,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_270_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(270)
        assert self.ship.heading == 270
        assert self.ship.rel_rot_coord_0 == (60, -20,)
        assert self.ship.rel_rot_coord_1 == (-60, -20,)
        assert self.ship.rel_rot_coord_2 ==  (-60, 20,)
        assert self.ship.rel_rot_coord_3 == (60, 20,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_quad_1_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(30)
        assert self.ship.heading == 30
        assert self.ship.rel_rot_coord_0 == (-47, -42,)
        assert self.ship.rel_rot_coord_1 == (13, 62,)
        assert self.ship.rel_rot_coord_2 ==  (47, 42,)
        assert self.ship.rel_rot_coord_3 == (-13, -62,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_quad_2_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(139)
        assert self.ship.heading == 139
        assert self.ship.rel_rot_coord_0 == (-24, 58,)
        assert self.ship.rel_rot_coord_1 == (54, -32,)
        assert self.ship.rel_rot_coord_2 == (24, -58,)
        assert self.ship.rel_rot_coord_3 == (-54, 32,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_quad_3_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(226)
        assert self.ship.heading == 226
        assert self.ship.rel_rot_coord_0 == (57, 27,)
        assert self.ship.rel_rot_coord_1 == (-29, -56,)
        assert self.ship.rel_rot_coord_2 == (-57, -27,)
        assert self.ship.rel_rot_coord_3 == (29, 56,)
        self._assert_heading_0_cords_fixed()

    def test_rotate_ship_to_quad_4_heading(self):
        self._assert_ship_heading_0()
        self.ship.cmd_set_heading(305)
        assert self.ship.heading == 305
        assert self.ship.rel_rot_coord_0 == (38, -51,)
        assert self.ship.rel_rot_coord_1 == (-61, 18,)
        assert self.ship.rel_rot_coord_2 == (-38, 51,)
        assert self.ship.rel_rot_coord_3 == (61, -18,)
        self._assert_heading_0_cords_fixed()


class TestShipCMDActivateAndDeactivateReactionWheel(TestCase):

    def setUp(self):
        self.ship = Ship.spawn(map_units_per_meter=10)
        self.ship.reaction_wheel_online = False

    def test_reaction_wheel_can_be_activated(self):
        assert not self.ship.reaction_wheel_online
        start_power = self.ship.battery_power
        self.ship.cmd_set_reaction_wheel_status(True)

        assert self.ship.reaction_wheel_online
        assert (
            self.ship.battery_power
            == (start_power - constants.ACTIVATE_REACTION_WHEEL_POWER_REQUIREMENT)
        )

    def test_reaction_wheel_cant_be_activated_if_not_enough_power(self):
        assert not self.ship.reaction_wheel_online
        self.ship.battery_power = constants.ACTIVATE_REACTION_WHEEL_POWER_REQUIREMENT // 2
        start_power = self.ship.battery_power
        self.ship.cmd_set_reaction_wheel_status(True)

        assert not self.ship.reaction_wheel_online
        assert self.ship.battery_power == start_power

    def test_reaction_wheel_can_be_shut_off(self):
        self.ship.reaction_wheel_online = True
        self.ship.cmd_set_reaction_wheel_status(False)
        assert not self.ship.reaction_wheel_online


class TestShipCMDActivateDeactivateLightEngine(TestCase):
    def setUp(self):
        self.ship = Ship.spawn(map_units_per_meter=10)

    def test_activate_engine_command_updates_ship_state(self):
        current_frame = 10
        assert self.ship._state == {}
        self.ship.game_frame = current_frame
        self.ship.cmd_activate_engine()
        assert self.ship._state == {
            ShipStateKey.ENGINE: {
                'starting': True,
                'last_frame': current_frame + self.ship.engine_frames_to_activate,
            }
        }

    def test_deactivate_engine_command_updates_ship_state(self):
        self.ship.engine_online = True
        self.ship.engine_lit = True
        self.ship.cmd_deactivate_engine()
        assert not self.ship.engine_online
        assert not self.ship.engine_lit

    def test_ship_engine_can_be_lit(self):
        self.ship.engine_online = True
        self.ship.engine_lit = False
        assert not self.ship.engine_lit
        self.ship.cmd_light_engine()
        assert self.ship.engine_lit
        assert self.ship.engine_online
