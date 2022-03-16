
import math
from typing import Tuple, Union, Optional

from api.constants import (
    ORGIN_COORD,
    DEGREES_NORTH,
    DEGREES_EAST,
    DEGREES_WEST,
    DEGREES_SOUTH,
    GENERAL_DIRECTION,
)


def rotate(origin: Tuple, point: Tuple, _angle: float) -> Tuple[int]:
    """ https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    """
    angle = _angle * -1 # Angle must be passed as radians
    ox, oy = origin
    px, py = point

    sine_angle = math.sin(angle)
    cos_angle = math.cos(angle)
    dx = px - ox
    dy = py - oy

    qx = ox + cos_angle * dx - sine_angle * dy
    qy = oy + sine_angle * dx + cos_angle * dy
    return round(qx), round(qy)


def degrees_to_radians(degrees: int) -> float:
    return math.radians(degrees)


def heading_to_delta_heading_from_zero(heading: int) -> int:
    return heading if heading <= 180 else (heading - 360)


def invert_heading(heading: int):
    if not (0 <= heading <= 360):
        raise Exception(f"cannot invert heading with value: {heading}")
    return heading - 180 if heading >= 180 else heading + 180


def signed_angle_to_unsigned_angle(degrees: int) -> int:
    if degrees >= 0:
        return degrees % 360

    pos_angle = abs(degrees)
    if pos_angle <= 360:
        return 360 - pos_angle
    else:
        return 360 - (pos_angle % 360)

def degree_is_cardinal(degree):
    return (signed_angle_to_unsigned_angle(degree) % 90) == 0

def degrees_to_general_direction(degree: int) -> str:
    u_degrees = signed_angle_to_unsigned_angle(degree)
    if 0 < u_degrees < 90:
        return GENERAL_DIRECTION.north_east_ish
    elif 90 < u_degrees < 180:
        return GENERAL_DIRECTION.south_east_ish
    elif 180 < u_degrees < 270:
        return GENERAL_DIRECTION.south_west_ish
    elif 270 < u_degrees < 360:
        return GENERAL_DIRECTION.north_west_ish
    raise Exception(f"received cardinal degree: {degree}")


def heading_to_rise_over_run_slope(degrees: int) -> float:
    # This does not handle cardinal headings: N/S/E/W AKA 0, 90, 180, 270, 360 etc..
    # It will raise a zero divizion error if you do.
    return round(1 / math.tan(degrees_to_radians(degrees)), 5)


def hitboxes_intercept_ray_factory(
    point: Tuple[int],
    heading: Union[int, float],
    map_dims: Tuple[int],
) -> Tuple:
    """ params
            point: a location on a grid
            heading: a direction (as degrees)
        returna tuple with
            0) function that when called will check if an array of hitbox lines falls on the ray.
            1) the point where the ray intercepts with the map's boundary
    """
    # point where the ray intercepts with the map's boundary.
    ray_point_b: Tuple[int]

    # Cardinal heading factory
    heading_is_cardinal = degree_is_cardinal(heading)
    if heading_is_cardinal:
        def inner_is_cardinal(hitbox_lines) -> Optional[bool]:
            if heading == DEGREES_NORTH:
                return (
                    # Any points on the hitbox are above line start.
                    any(hblp[1] > point[1] for hbl in hitbox_lines for hblp in hbl)
                    # Any line segments on the hitbox are vertically alligned.
                    and any( # TODO: do you need to check both line points?
                        (hbl[0][0] >= point[0] >= hbl[1][0]) or (hbl[0][0] <= point[0] <= hbl[1][0])
                        for hbl in hitbox_lines
                    )
                )
            elif heading == DEGREES_SOUTH:
                return (
                    # Any points on the hitbox are below line start.
                    any(hblp[1] < point[1] for hbl in hitbox_lines for hblp in hbl)
                    # Any line segments on the hitbox are vertically alligned.
                    and any(
                        (hbl[0][0] >= point[0] >= hbl[1][0]) or (hbl[0][0] <= point[0] <= hbl[1][0])
                        for hbl in hitbox_lines
                    )
                )
            elif heading == DEGREES_EAST:
                return (
                    # Any points on the hitbox are to the right of line start.
                    any(hblp[0] > point[0] for hbl in hitbox_lines for hblp in hbl)
                    # Any line segments on the hitbox are horizontally alligned.
                    and any(
                        (hbl[0][1] >= point[1] >= hbl[1][1]) or (hbl[0][1] <= point[1] <= hbl[1][1])
                        for hbl in hitbox_lines
                    )
                )
            elif heading == DEGREES_WEST:
                return (
                    # Any points on the hitbox are to the left of line start.
                    any(hblp[0] < point[0] for hbl in hitbox_lines for hblp in hbl)
                    # Any line segments on the hitbox are horizontally alligned.
                    and any(
                        (hbl[0][1] >= point[1] >= hbl[1][1]) or (hbl[0][1] <= point[1] <= hbl[1][1])
                        for hbl in hitbox_lines
                    )
                )
            else:
                raise NotImplementedError

        if heading == DEGREES_NORTH:
            ray_point_b = (point[0], map_dims[1])
        elif heading == DEGREES_EAST:
            ray_point_b = (map_dims[0], point[1])
        elif heading == DEGREES_SOUTH:
            ray_point_b = (point[0], 0)
        elif heading == DEGREES_WEST:
            ray_point_b = (0, point[1])
        else:
            raise NotImplementedError

        return inner_is_cardinal, ray_point_b

    # Non-Cardinal heading factory
    ror_slope = heading_to_rise_over_run_slope(heading)
    general_direction = degrees_to_general_direction(heading)
    if general_direction == GENERAL_DIRECTION.north_east_ish:
        ray_point_b = (
            # X
            point[0] + map_dims[0],
            # Y
            round(point[1] + map_dims[0] * ror_slope), # ror_slope is positive
        )
    elif general_direction == GENERAL_DIRECTION.south_east_ish:
        ray_point_b = (
            # X
            point[0] + map_dims[0],
            # Y
            round(point[1] + map_dims[0] * ror_slope), # ror_slope is negative
        )
    elif general_direction == GENERAL_DIRECTION.south_west_ish:
        ray_point_b = (
            # X
            point[0] - map_dims[0],
            # Y
            round(point[1] - map_dims[0] * ror_slope), # ror_slope is positive
        )
    elif general_direction == GENERAL_DIRECTION.north_west_ish:
        ray_point_b = (
            # X
            point[0] - map_dims[0],
            # Y
            round(point[1] - map_dims[0] * ror_slope), # ror_slope is negative
        )
    else:
        raise NotImplementedError

    def _ccw(A,B,C):
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

    def _intersect(A,B,C,D):
        # Return true if line segments AB and CD intersect
        # Thanks https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect
        # Does not deal well with collinearity (so they say)
        #   grid squares are going to be small so we'll say
        #   for a hit on a hitbox to count its perimeter must be pierced by the ray.
        return _ccw(A,C,D) != _ccw(B,C,D) and _ccw(A,B,C) != _ccw(A,B,D)

    def inner_is_not_cardinal(hitbox_lines) -> Optional[bool]:
        if general_direction == GENERAL_DIRECTION.north_east_ish:
            # TODO: only checking hbl point 1. do I need tocheck hbl point 2?
            if any((hbl[0][0] > point[0] and hbl[0][1] > point[1]) for hbl in hitbox_lines):
                # hitbox lines do run through point's NE sector.
                return any(
                    _intersect(hbl[0], hbl[1], point, ray_point_b)
                    for hbl in hitbox_lines
                )
        if general_direction == GENERAL_DIRECTION.south_east_ish:
            if any((hbl[0][0] > point[0] and hbl[0][1] < point[1]) for hbl in hitbox_lines):
                # hitbox lines do run through point's SE sector.
                return any(
                    _intersect(hbl[0], hbl[1], point, ray_point_b)
                    for hbl in hitbox_lines
                )
        if general_direction == GENERAL_DIRECTION.south_west_ish:
            if any((hbl[0][0] < point[0] and hbl[0][1] < point[1]) for hbl in hitbox_lines):
                # hitbox lines do run through point's SW sector.
                return any(
                    _intersect(hbl[0], hbl[1], point, ray_point_b)
                    for hbl in hitbox_lines
                )
        if general_direction == GENERAL_DIRECTION.north_west_ish:
            if any((hbl[0][0]< point[0] and hbl[0][1] > point[1]) for hbl in hitbox_lines):
                # hitbox lines do run through point's NW sector.
                return any(
                    _intersect(hbl[0], hbl[1], point, ray_point_b)
                    for hbl in hitbox_lines
                )

    return inner_is_not_cardinal, ray_point_b


def translate_point(point: Tuple, degrees: int, distance_map_units: int) -> Tuple:
    px, py = point
    radians = degrees_to_radians(degrees % 360)
    px += (distance_map_units * math.sin(radians))
    py += (distance_map_units * math.cos(radians))
    return round(px), round(py)


def calculate_resultant_vector(fx: Union[int, float], fy: Union[int, float]) -> Tuple:
    """ Given an X and Y force component, calculate the resultant force.
        Return resultant force as distance (meters) and direction (heading)
    """
    if fy == 0 and fx == 0:
        return (0, 0,)

    meters = math.sqrt((fx**2) + (fy**2))

    if fy != 0:
        angle = math.degrees(math.atan(fx / fy))
    elif fy == 0 and fx > 0:
        angle = 90
    elif fy == 0 and fx < 0:
        angle = 270
    else:
        raise NotImplementedError

    x_negative = fx < 0
    y_negative = fy < 0
    both_positive = (not x_negative) and (not y_negative)
    both_negative = x_negative and y_negative

    if both_positive:
        return (
            meters,
            round(angle),
        )
    elif both_negative:
        return (
            meters,
            invert_heading(round(angle)),
        )
    elif y_negative:
        return (
            meters,
            invert_heading(signed_angle_to_unsigned_angle(round(angle))),
        )
    elif x_negative:
        return (
            meters,
            signed_angle_to_unsigned_angle(round(angle)),
        )
    else:
        raise NotImplementedError


def calculate_x_y_components(
    meters: Union[int, float],
    heading: int,
) -> Tuple[float]:
    """ Given distance and direction, convert to X, Y force components
    """
    if meters == 0:
        return ORGIN_COORD
    degrees = signed_angle_to_unsigned_angle(heading)
    radians = degrees_to_radians(degrees)
    return (
        (meters * math.sin(radians)),
        (meters * math.cos(radians)),
    )


def calculate_point_distance(point_a: Tuple, point_b: Tuple) -> float:
    ax, ay = point_a
    bx, by = point_b
    return math.sqrt(((bx - ax) ** 2) + ((by - ay) ** 2))


def calculate_heading_to_point(point_a: Tuple, point_b: Tuple) -> float:
    x1, y1 = point_a
    x2, y2 = point_b
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return 0

    x_negative = dx < 0
    y_negative = dy < 0
    both_positive = (not x_negative) and (not y_negative)
    both_negative = x_negative and y_negative

    if dy != 0:
        angle = math.degrees(math.atan(dx / dy))
    elif dy == 0 and dx > 0:
        angle = 90
    elif dy == 0 and dx < 0:
        angle = 270
    else:
        return 0 # dx and dy are both 0

    if both_positive:
        return angle
    elif both_negative:
        return invert_heading(angle)
    elif y_negative:
        return invert_heading(signed_angle_to_unsigned_angle(angle))
    elif x_negative:
        return signed_angle_to_unsigned_angle(angle)
    else:
        raise NotImplementedError
