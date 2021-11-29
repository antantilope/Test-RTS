
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
