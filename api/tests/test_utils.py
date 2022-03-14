
from unittest import TestCase

from api import utils2d
from api import constants

class TestUtils(TestCase):

    origin = constants.ORGIN_COORD

    def test_heading_to_delta_heading_from_zero(self):
        assert utils2d.heading_to_delta_heading_from_zero(45) == 45
        assert utils2d.heading_to_delta_heading_from_zero(90) == 90
        assert utils2d.heading_to_delta_heading_from_zero(180) == 180
        assert utils2d.heading_to_delta_heading_from_zero(181) == -179
        assert utils2d.heading_to_delta_heading_from_zero(270) == -90
        assert utils2d.heading_to_delta_heading_from_zero(359) == -1


    def test_signed_angle_to_unsigned_angle(self):
        # Positive angles
        assert utils2d.signed_angle_to_unsigned_angle(0) == 0
        assert utils2d.signed_angle_to_unsigned_angle(44) == 44
        assert utils2d.signed_angle_to_unsigned_angle(75) == 75
        assert utils2d.signed_angle_to_unsigned_angle(185) == 185
        assert utils2d.signed_angle_to_unsigned_angle(299) == 299
        assert utils2d.signed_angle_to_unsigned_angle(344) == 344
        assert utils2d.signed_angle_to_unsigned_angle(360) == 0
        assert utils2d.signed_angle_to_unsigned_angle(360 + 150) == 150
        assert utils2d.signed_angle_to_unsigned_angle(360 * 3 + 299) == 299

        # Negative angles
        assert utils2d.signed_angle_to_unsigned_angle(-44) == 360 - 44
        assert utils2d.signed_angle_to_unsigned_angle(-75) == 360 - 75
        assert utils2d.signed_angle_to_unsigned_angle(-185) == 360 - 185
        assert utils2d.signed_angle_to_unsigned_angle(-299) == 360 - 299
        assert utils2d.signed_angle_to_unsigned_angle(-344) == 360 - 344
        assert utils2d.signed_angle_to_unsigned_angle(-360) == 0
        assert utils2d.signed_angle_to_unsigned_angle(-370) == 360 - 10

    def test_invert_heading(self):
        assert utils2d.invert_heading(0) == 180
        assert utils2d.invert_heading(180) == 0
        assert utils2d.invert_heading(90) == 270
        assert utils2d.invert_heading(270) == 90


    # ANGLE ROTATIONS # # #

    def test_360_rotation_results_in_same_point(self):
        rotation = utils2d.degrees_to_radians(360)
        point = (-42, 33)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == point
        rotation = utils2d.degrees_to_radians(-360)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == point


    def test_rotate_point_180(self):
        rotation = utils2d.degrees_to_radians(180)

        point = (2, 5)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-2, -5)

        point = (-5, 2)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (5, -2)

        point = (-4, -8)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (4, 8)

        point = (6, -3)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-6, 3)


    def test_rotate_point_negative_180(self):
        rotation = utils2d.degrees_to_radians(-180)

        point = (2, 5)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-2, -5)

        point = (-5, 2)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (5, -2)

        point = (-4, -8)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (4, 8)

        point = (6, -3)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-6, 3)


    def test_rotate_point_90(self):
        rotation = utils2d.degrees_to_radians(90)

        point = (2, 5)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (5, -2)

        point = (-5, 2)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (2, 5)

        point = (-5, -2)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-2, 5)

        point = (-4, 3)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (3, 4)


    def test_rotate_point_negative_90(self):
        rotation = utils2d.degrees_to_radians(-90)

        point = (5, -2)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (2, 5)

        point = (2, 5)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-5, 2)

        point = (-2, 5)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-5, -2)

        point = (3, 4)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-4, 3)


    def test_rotate_quad_1_point_40_degrees(self):
        rotation = utils2d.degrees_to_radians(40)
        point = (60, 75)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (94, 19,)


    def test_rotate_quad_1_point_negative_40_degrees(self):
        rotation = utils2d.degrees_to_radians(-40)
        point = (60, 75)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-2, 96,)


    def test_rotate_quad_2_point_40_degrees(self):
        rotation = utils2d.degrees_to_radians(40)
        point = (3, -50)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-30, -40,)


    def test_rotate_quad_2_point_negative_40_degrees(self):
        rotation = utils2d.degrees_to_radians(-40)
        point = (3, -50)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (34, -36,)


    def test_rotate_quad_3_point_60_degrees(self):
        rotation = utils2d.degrees_to_radians(60)
        point = (-63, -50)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-75, 30,)


    def test_rotate_quad_3_point_negative_60_degrees(self):
        rotation = utils2d.degrees_to_radians(-60)
        point = (-63, -50)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (12, -80,)


    def test_rotate_quad_4_point_66_degrees(self):
        rotation = utils2d.degrees_to_radians(66)
        point = (-42, 33)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (13, 52,)


    def test_rotate_quad_4_point_negative_66_degrees(self):
        rotation = utils2d.degrees_to_radians(-66)
        point = (-42, 33)
        rotated = utils2d.rotate(self.origin, point, rotation)
        assert rotated == (-47, -25,)


    # Angle measurement
    def test_calculate_heading_to_point(self):
        # north
        assert round(utils2d.calculate_heading_to_point(
            (0, 0), (0, 6)
        )) == constants.DEGREES_NORTH
        assert round(utils2d.calculate_heading_to_point(
            (2, -12), (2, 5)
        )) == constants.DEGREES_NORTH
        assert round(utils2d.calculate_heading_to_point(
            (-4, -7), (-4, 1000)
        )) == constants.DEGREES_NORTH

        # south
        assert round(utils2d.calculate_heading_to_point(
            (0, 6), (0, 2)
        )) == constants.DEGREES_SOUTH
        assert round(utils2d.calculate_heading_to_point(
            (2, -12), (2, -20)
        )) == constants.DEGREES_SOUTH
        assert round(utils2d.calculate_heading_to_point(
            (-4, 1000), (-4, 250)
        )) == constants.DEGREES_SOUTH

        # east
        assert round(utils2d.calculate_heading_to_point(
            (0, 6), (8, 6)
        )) == constants.DEGREES_EAST
        assert round(utils2d.calculate_heading_to_point(
            (2, -12), (12, -12)
        )) == constants.DEGREES_EAST
        assert round(utils2d.calculate_heading_to_point(
            (-4, 1000), (0, 1000)
        )) == constants.DEGREES_EAST

        # west
        assert round(utils2d.calculate_heading_to_point(
            (0, 6), (-8, 6)
        )) == constants.DEGREES_WEST
        assert round(utils2d.calculate_heading_to_point(
            (2, -12), (-12, -12)
        )) == constants.DEGREES_WEST
        assert round(utils2d.calculate_heading_to_point(
            (-4, 1000), (-12, 1000)
        )) == constants.DEGREES_WEST

        # NW/SW/NE/SE
        assert round(utils2d.calculate_heading_to_point(
            (0, 0), (6, 6)
        )) == constants.DEGREES_NORTH_EAST
        assert round(utils2d.calculate_heading_to_point(
            (0, 0), (6, -6)
        )) == constants.DEGREES_SOUTH_EAST
        assert round(utils2d.calculate_heading_to_point(
            (0, 0), (-6, -6)
        )) == constants.DEGREES_SOUTH_WEST
        assert round(utils2d.calculate_heading_to_point(
            (0, 0), (-6, 6)
        )) == constants.DEGREES_NORTH_WEST

        # Misc South Westernly angles
        assert (round(utils2d.calculate_heading_to_point(
            (9, 4), (-3, -6)
        ))) == 230
        assert (round(utils2d.calculate_heading_to_point(
            (9, 1), (-12, -1)
        ))) == 265
        assert (round(utils2d.calculate_heading_to_point(
            (-3, -2), (-25, -3)
        ))) == 267
        assert (round(utils2d.calculate_heading_to_point(
            (10, 10), (8, 0)
        ))) == 191

        # Misc North Westernly angles
        assert (round(utils2d.calculate_heading_to_point(
            (10, 10), (-3, 22)
        ))) == 313
        assert (round(utils2d.calculate_heading_to_point(
            (2, -10), (-12, -8)
        ))) == 278
        assert (round(utils2d.calculate_heading_to_point(
            (7, 7), (-25, 8)
        ))) == 272
        assert (round(utils2d.calculate_heading_to_point(
            (-10, -10), (-11, 10)
        ))) == 357

        # Misc North Easternly angles
        assert (round(utils2d.calculate_heading_to_point(
            (2, 3), (12, 5)
        ))) == 79
        assert (round(utils2d.calculate_heading_to_point(
            (2, 3), (12, 100)
        ))) == 6
        assert (round(utils2d.calculate_heading_to_point(
            (-2, 2), (1, 9)
        ))) == 23
        assert (round(utils2d.calculate_heading_to_point(
            (-2, -20), (25, -3)
        ))) == 58
        assert (round(utils2d.calculate_heading_to_point(
            (-10, -10), (5, 4)
        ))) == 47

        # Misc South Easternly angles
        assert (round(utils2d.calculate_heading_to_point(
            (12, 17), (23, 5)
        ))) == 137
        assert (round(utils2d.calculate_heading_to_point(
            (2, 12), (3, -10)
        ))) == 177
        assert (round(utils2d.calculate_heading_to_point(
            (-12, 2), (12, -1)
        ))) == 97
        assert (round(utils2d.calculate_heading_to_point(
            (-12, 12), (4, 7)
        ))) == 107


        # Try with the same exact point
        assert (round(utils2d.calculate_heading_to_point(
            (-12, 12), (-12, 12)
        ))) == 0


    # RESULTANT FORCE # # #
    def test_calc_resultant_force_due_north(self):
        meters, angle = utils2d.calculate_resultant_vector(0, 12)
        assert round(meters) == 12
        assert angle == 0 # N

    def test_calc_resultant_force_due_east(self):
        meters, angle = utils2d.calculate_resultant_vector(12, 0)
        assert round(meters) == 12
        assert angle == 90 # E

    def test_calc_resultant_force_due_south(self):
        meters, angle = utils2d.calculate_resultant_vector(0, -12)
        assert round(meters) == 12
        assert angle == 180 # S

    def test_calc_resultant_force_due_west(self):
        meters, angle = utils2d.calculate_resultant_vector(-12, 0)
        assert round(meters) == 12
        assert angle == 270 # W

    def test_calc_quad_1_resultant_force(self):
        meters, angle = utils2d.calculate_resultant_vector(19, 12)
        assert round(meters) == 22
        assert angle == 58

    def test_calc_quad_1_resultant_force_xy_equal(self):
        meters, angle = utils2d.calculate_resultant_vector(19, 19)
        assert round(meters) == 27
        assert angle == 45 # NE

    def test_calc_quad_2_resultant_force(self):
        meters, angle = utils2d.calculate_resultant_vector(9, -7)
        assert round(meters) == 11
        assert angle == 128

    def test_calc_quad_2_resultant_force_xy_equal(self):
        meters, angle = utils2d.calculate_resultant_vector(8, -8)
        assert round(meters) == 11
        assert angle == 135 # SE

    def test_calc_quad_3_resultant_force(self):
        meters, angle = utils2d.calculate_resultant_vector(-17, -12)
        assert round(meters) == 21
        assert angle == 235

    def test_calc_quad_3_resultant_force_xy_equal(self):
        meters, angle = utils2d.calculate_resultant_vector(-17, -17)
        assert round(meters) == 24
        assert angle == 225 # SW

    def test_calc_quad_4_resultant_force(self):
        meters, angle = utils2d.calculate_resultant_vector(-13, 21)
        assert round(meters) == 25
        assert angle == 328

    def test_calc_quad_4_resultant_force_xy_equal(self):
        meters, angle = utils2d.calculate_resultant_vector(-14, 14)
        assert round(meters) == 20
        assert angle == 315 # NW


    # FORCE COMPONENETS # # #

    def _calculate_x_y_components(self, *args):
        return tuple(map(round, utils2d.calculate_x_y_components(*args)))

    def test_calc_components_for_vector_with_no_magnitude(self):
        assert self._calculate_x_y_components(0, 135) == constants.ORGIN_COORD

    def test_calc_components_for_n_vector(self):
        x, y = self._calculate_x_y_components(12, 0)
        assert (x, y) == (0, 12)
        x, y = self._calculate_x_y_components(12, 360) # 0 and 360 are equivolent.
        assert (x, y) == (0, 12)

    def test_calc_components_for_s_vector(self):
        x, y = self._calculate_x_y_components(12, 180)
        assert (x, y) == (0, -12)

    def test_calc_components_for_e_vector(self):
        x, y = self._calculate_x_y_components(12, 90)
        assert (x, y) == (12, 0)

    def test_calc_components_for_w_vector(self):
        x, y = self._calculate_x_y_components(12, 270)
        assert (x, y) == (-12, 0)

    def test_calc_components_for_ne_vector(self):
        x, y = self._calculate_x_y_components(12, 28)
        assert (x, y) == (6, 11)
        x, y = self._calculate_x_y_components(12, 45)
        assert (x, y) == (8, 8)
        x, y = self._calculate_x_y_components(12, 70)
        assert (x, y) == (11, 4)

    def test_calc_components_for_se_vector(self):
        x, y = self._calculate_x_y_components(12, 110)
        assert (x, y) == (11, -4)
        x, y = self._calculate_x_y_components(12, 135)
        assert (x, y) == (8, -8)
        x, y = self._calculate_x_y_components(12, 160)
        assert (x, y) == (4, -11)

    def test_calc_components_for_sw_vector(self):
        x, y = self._calculate_x_y_components(12, 200)
        assert (x, y) == (-4, -11)
        x, y = self._calculate_x_y_components(12, 225)
        assert (x, y) == (-8, -8)
        x, y = self._calculate_x_y_components(12, 250)
        assert (x, y) == (-11, -4)

    def test_calc_components_for_nw_vector(self):
        x, y = self._calculate_x_y_components(12, 290)
        assert (x, y) == (-11, 4)
        x, y = self._calculate_x_y_components(12, 315)
        assert (x, y) == (-8, 8)
        x, y = self._calculate_x_y_components(12, 340)
        assert (x, y) == (-4, 11)


    # POINT TRANSLATION # # #

    def test_translate_point_move_n(self):
        start = (12, 12,)
        heading = 0
        distance = 25
        end = utils2d.translate_point(start, heading, distance)
        assert end == (12, 37,)

    def test_translate_point_move_s(self):
        start = (12, 12,)
        heading = 180
        distance = 10
        end = utils2d.translate_point(start, heading, distance)
        assert end == (12, 2,)

    def test_translate_point_move_e(self):
        start = (12, 12,)
        heading = 90
        distance = 10
        end = utils2d.translate_point(start, heading, distance)
        assert end == (22, 12,)

    def test_translate_point_move_w(self):
        start = (12, 12,)
        heading = 270
        distance = 10
        end = utils2d.translate_point(start, heading, distance)
        assert end == (2, 12,)

    def test_translate_point_move_ne(self):
        start = (12, 12,)
        heading = 45
        distance = 25
        end = utils2d.translate_point(start, heading, distance)
        assert end == (30, 30,)

    def test_translate_point_move_se(self):
        start = (12, 12,)
        heading = 110
        distance = 10
        end = utils2d.translate_point(start, heading, distance)
        assert end == (21, 9,)

    def test_translate_point_move_sw(self):
        start = (12, 12,)
        heading = 225
        distance = 10
        end = utils2d.translate_point(start, heading, distance)
        assert end == (5, 5,)

    def test_translate_point_move_nw(self):
        start = (12, 12,)
        heading = 315
        distance = 10
        end = utils2d.translate_point(start, heading, distance)
        assert end == (5, 19,)

    def test_calculate_point_distance(self):
        assert round(utils2d.calculate_point_distance((0, 0), (0, 8))) == 8
        assert round(utils2d.calculate_point_distance((0, 0), (0, -8))) == 8
        assert round(utils2d.calculate_point_distance((0, 0), (8, 0))) == 8
        assert round(utils2d.calculate_point_distance((0, 0), (-8, 0))) == 8
        assert round(utils2d.calculate_point_distance((0, 8), (0, 0))) == 8
        assert round(utils2d.calculate_point_distance((0, -8), (0, 0))) == 8
        assert round(utils2d.calculate_point_distance((8, 0), (0, 0))) == 8
        assert round(utils2d.calculate_point_distance((-8, 0), (0, 0))) == 8
        assert round(utils2d.calculate_point_distance((-4, -4), (8, 8))) == 17
        assert round(utils2d.calculate_point_distance((8, 8), (-4, -4))) == 17

    def test_degrees_to_general_direction(self):
        assert utils2d.degrees_to_general_direction(10) == constants.GENERAL_DIRECTION.north_east_ish
        assert utils2d.degrees_to_general_direction(80) == constants.GENERAL_DIRECTION.north_east_ish
        assert utils2d.degrees_to_general_direction(360 + 10) == constants.GENERAL_DIRECTION.north_east_ish
        assert utils2d.degrees_to_general_direction(360 + 80) == constants.GENERAL_DIRECTION.north_east_ish
        assert utils2d.degrees_to_general_direction(100) == constants.GENERAL_DIRECTION.south_east_ish
        assert utils2d.degrees_to_general_direction(170) == constants.GENERAL_DIRECTION.south_east_ish
        assert utils2d.degrees_to_general_direction(190) == constants.GENERAL_DIRECTION.south_west_ish
        assert utils2d.degrees_to_general_direction(260) == constants.GENERAL_DIRECTION.south_west_ish
        assert utils2d.degrees_to_general_direction(280) == constants.GENERAL_DIRECTION.north_west_ish
        assert utils2d.degrees_to_general_direction(350) == constants.GENERAL_DIRECTION.north_west_ish

    def test_degree_is_cardinal(self):
        cardinals = [0, 90, 180, 270, 360]
        for degree in range(360):
            assert utils2d.degree_is_cardinal(degree) is (degree in cardinals)

    def assert_floats_equal(self, f1, f2):
        self.assertEqual(round(f1, 5), round(f2, 5))

    def test_heading_to_rise_over_run_slope(self):
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(1),
            57.28996,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(2),
            28.63625,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(10),
            5.67128,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(45),
            1.0,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(55),
            0.70021,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(85),
            0.08749,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(92),
            -0.03492,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(135),
            -1.0,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(145),
            -1.42815,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(165),
            -3.73205,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(178),
            -28.63625,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(179),
            -57.28996,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(181),
            57.28996,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(182),
            28.63625,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(190),
            5.67128,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(225),
            1.0,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(245),
            0.46631,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(265),
            0.08749,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(269),
            0.01746,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(271),
            -0.01746,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(290),
            -0.36397,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(315),
            -1.0,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(345),
            -3.73205,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(358),
            -28.63625,
        )
        self.assert_floats_equal(
            utils2d.heading_to_rise_over_run_slope(359),
            -57.28996,
        )


    def test_hitboxes_intercept_ray_factory_returns_a_callable(self):
        # Cardinal factory
        calculator = utils2d.hitboxes_intercept_ray_factory((0, 0), constants.DEGREES_NORTH)
        assert callable(calculator) is True
        # Non-Cardinal factory
        calculator = utils2d.hitboxes_intercept_ray_factory((0, 0), 23, (1000, 1000))
        assert callable(calculator) is True

    def flip_hbls(self, hbls):
        # relative line segments representing a ship's hitbox are flipped if ship's heading is >= 180
        # when testing geometry it's good to flip line-segment points to ensure
        # logic is agnostic to rotated points. (Bad explanation, I know).
        return tuple(
            tuple(reversed(ls)) for ls in hbls
        )

    def test_hitboxes_intercept_ray_factory_due_north(self):
        hbls = (
            ((100, 100), (100, 120),),
            ((100, 120), (110, 120),),
            ((110, 120), (110, 100),),
            ((110, 100), (100, 100),),
        )

        start_point = (99, 21) # Start is too far to the left.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_NORTH)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False
        start_point = (112, 21) # Start is too far to the right.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_NORTH)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False
        start_point = (105, 150) # Start is above the target.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_NORTH)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False

        start_point = (100, 21)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_NORTH)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (103, 21)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_NORTH)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (108, 21)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_NORTH)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (110, 21)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_NORTH)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True

    def test_hitboxes_intercept_ray_factory_due_south(self):
        hbls = (
            ((100, 100), (100, 120),),
            ((100, 120), (110, 120),),
            ((110, 120), (110, 100),),
            ((110, 100), (100, 100),),
        )

        start_point = (99, 321) # Start is too far to the left.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_SOUTH)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False
        start_point = (112, 321) # Start is too far to the right.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_SOUTH)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False
        start_point = (105, 21) # Start is above the target.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_SOUTH)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False

        start_point = (100, 321)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_SOUTH)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (103, 321)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_SOUTH)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (108, 321)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_SOUTH)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (110, 321)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_SOUTH)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True

    def test_hitboxes_intercept_ray_factory_due_east(self):
        hbls = (
            ((100, 100), (100, 120),),
            ((100, 120), (110, 120),),
            ((110, 120), (110, 100),),
            ((110, 100), (100, 100),),
        )

        start_point = (10, 121) # Start is too far up.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_EAST)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False
        start_point = (10, 99) # Start is too far down.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_EAST)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False
        start_point = (130, 110) # Start is too far east.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_EAST)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False

        start_point = (10, 100)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_EAST)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (10, 103)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_EAST)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (10, 108)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_EAST)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (10, 120)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_EAST)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True

    def test_hitboxes_intercept_ray_factory_due_west(self):
        hbls = (
            ((100, 100), (100, 120),),
            ((100, 120), (110, 120),),
            ((110, 120), (110, 100),),
            ((110, 100), (100, 100),),
        )

        start_point = (200, 121) # Start is too far up.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_WEST)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False
        start_point = (200, 99) # Start is too far down.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_WEST)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False
        start_point = (70, 110) # Start is too far west.
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_WEST)
        assert calculator(hbls) is False
        assert calculator(self.flip_hbls(hbls)) is False

        start_point = (200, 100)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_WEST)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (200, 108)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_WEST)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (200, 117)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_WEST)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True
        start_point = (200, 120)
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, constants.DEGREES_WEST)
        assert calculator(hbls) is True
        assert calculator(self.flip_hbls(hbls)) is True

    def test_hitboxes_intercept_ray_factory_north_east_ish_nne(self):
        hbls = (
            ((10, 21), (12, 22),),
            ((12, 22), (9, 24),),
            ((9, 24), (8, 23),),
            ((8, 23), (10, 21))
        )
        start_point = (3, 3)

        # direct hit
        heading = 18
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        # traverse up
        heading = 17
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 16
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 15
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 14
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is False
        # traverse down
        heading = 20
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 22
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 24
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 26
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is False

    def test_hitboxes_intercept_ray_factory_north_east_ish_ene(self):
        hbls = (
            ((10, 21), (12, 22),),
            ((12, 22), (9, 24),),
            ((9, 24), (8, 23),),
            ((8, 23), (10, 21))
        )
        start_point = (-25, 15)

        # direct hit
        heading = 77
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        # traverse up
        heading = 76
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 75
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is False
        # traverse down
        heading = 78
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 79
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 80
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 81
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is False


    def test_hitboxes_intercept_ray_factory_south_east_ish_ese(self):
        hbls = (
            ((10, 21), (12, 22),),
            ((12, 22), (9, 24),),
            ((9, 24), (8, 23),),
            ((8, 23), (10, 21))
        )
        start_point = (-25, 32)

    def test_hitboxes_intercept_ray_factory_south_east_ish_sse(self):
        hbls = (
            ((10, 21), (12, 22),),
            ((12, 22), (9, 24),),
            ((9, 24), (8, 23),),
            ((8, 23), (10, 21))
        )
        start_point = (5, 50)

    def test_hitboxes_intercept_ray_factory_north_west_ish_wnw(self):
        hbls = (
            ((10, 21), (12, 22),),
            ((12, 22), (9, 24),),
            ((9, 24), (8, 23),),
            ((8, 23), (10, 21))
        )
        start_point = (28, 16)

        # direct hit
        heading = 288
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        # traverse up
        heading = 290
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 292
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 294
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is False
        # traverse down
        heading = 286
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is True
        heading = 284
        calculator = utils2d.hitboxes_intercept_ray_factory(start_point, heading, (100, 100))
        assert calculator(hbls) is False
