
import math
from typing import Tuple, Optional, Union

from api.constants import ORGIN_COORD


def rotate(origin: Tuple, point: Tuple, _angle: float) -> Tuple[int]:
    """ https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    """
    angle = _angle * -1
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


def calculate_resultant_vector(fx: int, fy: int) -> Tuple:
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


def translate_point(point: Tuple, degrees: int, distance_map_units: int) -> Tuple:
    px, py = point
    radians = degrees_to_radians(degrees % 360)
    px += (distance_map_units * math.sin(radians))
    py += (distance_map_units * math.cos(radians))
    return round(px), round(py)
