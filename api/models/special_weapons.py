
from typing import Tuple

from api.models.base import BaseModel
from api import constants
from api import utils2d


class MagnetMine(BaseModel):
    """ Guided explosive munition (dumb acceleration model)
        that tracks any closest ship (including the shooter).
        Arms after a short period.
        explodes within proximity killing all ships
        within a large AOE.
    """

    def __init__(self, game_frame: int, ship_id: str):
        super().__init__()
        self.elapsed_milliseconds = 0
        self.created_frame = game_frame
        self.ship_id = ship_id

        self.armed = False
        self.percent_armed = 0
        self.exploded = False

        # Position
        self.coord_x = 0
        self.coord_y = 0

        # Velocity
        self.velocity_x_meters_per_second = float(0)
        self.velocity_y_meters_per_second = float(0)

        self.closest_ship_id = None
        self.distance_to_closest_ship = None

    @property
    def coords(self):
        return (self.coord_x, self.coord_y,)


class EMP(BaseModel):
    """ Unguided munition. Arms after a number of seconds.
        Explodes within proximity of any ship.
        AOE effect that deactivates all systems and drains power.
    """

    def __init__(self, game_frame: int, ship_id: str):
        super().__init__()
        self.elapsed_milliseconds = 0
        self.created_frame = game_frame
        self.ship_id = ship_id

        self.armed = False
        self.percent_armed = 0
        self.exploded = False

        # Position
        self.coord_x = 0
        self.coord_y = 0

        # Velocity
        self.velocity_x_meters_per_second = float(0)
        self.velocity_y_meters_per_second = float(0)

    @property
    def coords(self):
        return (self.coord_x, self.coord_y,)


class HunterDrone(BaseModel):
    """ guided munition that patroles
        and tracks (smart acceleration model)
        first enemy ship encountered.
        explodes within proximity killing all ships
        within a small AOE.
    """

    AUTOPILOT_MODE_PATROL = "patrol"
    AUTOPILOT_PATROL_PATERN_CLOCKWISE = "cw"
    AUTOPILOT_PATROL_PATERN_COUNTERCLOCKWISE = "ccw"
    AUTOPILOT_MODE_CHASE = "chase"

    def __init__(
        self,
        map_units_per_meter: int,
        game_frame: int,
        ship_id: str,
        initial_heading: int,
        initial_velocity_x_meters_per_second: float,
        initial_velocity_y_meters_per_second: float,
        coord_x: int,
        coord_y: int,
    ):
        super().__init__()
        self.elapsed_milliseconds = 0
        self.created_frame = game_frame
        self.ship_id = ship_id

        self.exploded = False

        # Position
        self.coord_x = coord_x
        self.coord_y = coord_y

        # Velocity
        self.velocity_x_meters_per_second = float(initial_velocity_x_meters_per_second)
        self.velocity_y_meters_per_second = float(initial_velocity_y_meters_per_second)
        # Acceleration
        self._tracking_acceleration = constants.HUNTER_DRONE_TRACKING_ACCELERATION_MS

        # Heading of drone in degrees (between 0 and 359)
        self.heading = None

        # Orient hit boxes
        x_len = constants.HUNTER_DRONE_X_LEN * map_units_per_meter
        y_len = constants.HUNTER_DRONE_Y_LEN * map_units_per_meter
        # relative hitbox coordinates
        # of the drone with heading fixed to zero.
        # These coords will NOT change
        nose_x = 0
        nose_y = round(y_len / 2)
        bottom_left_x = round((x_len / 2) * -1)
        bottom_right_x = round(x_len / 2)
        bottom_y = round(y_len / 2 * -1)
        self.rel_fixed_coord_hitbox_nose = (nose_x, nose_y, )
        self.rel_fixed_coord_hitbox_bottom_left = (bottom_left_x, bottom_y, )
        self.rel_fixed_coord_hitbox_bottom_right = (bottom_right_x, bottom_y, )
        # These are the coordinates for the drone if the drone's center is at the origin: (coord_x, coord_y) == (0, 0,)
        # Relative rotated hitbox coordinates
        # these values are rotated to account for drone heading.
        self.rel_rot_coord_hitbox_nose = (
            self.rel_fixed_coord_hitbox_nose[0] + self.coord_x,
            self.rel_fixed_coord_hitbox_nose[1] + self.coord_y,
        )
        self.rel_rot_coord_hitbox_bottom_left = (
            self.rel_fixed_coord_hitbox_bottom_left[0] + self.coord_x,
            self.rel_fixed_coord_hitbox_bottom_left[1] + self.coord_y,
        )
        self.rel_rot_coord_hitbox_bottom_right = (
            self.rel_fixed_coord_hitbox_bottom_right[0] + self.coord_x,
            self.rel_fixed_coord_hitbox_bottom_right[1] + self.coord_y,
        )

        self.set_heading(initial_heading)

        # autopilot
        self.autopilot_mode = self.AUTOPILOT_MODE_PATROL
        if initial_heading < 180:
            self.autopilot_patrol_pattern = self.AUTOPILOT_PATROL_PATERN_CLOCKWISE
        else:
            self.autopilot_patrol_pattern = self.AUTOPILOT_PATROL_PATERN_COUNTERCLOCKWISE

    @property
    def coords(self) -> Tuple[int]:
        return (self.coord_x, self.coord_y,)

    def set_heading(self, heading: int):
        self.heading = heading
        self._set_relative_coords()


    def _set_relative_coords(self) -> None:
        delta_radians = utils2d.degrees_to_radians(
            utils2d.heading_to_delta_heading_from_zero(self.heading)
        )
        self.rel_rot_coord_hitbox_nose = utils2d.rotate(
            constants.ORGIN_COORD,
            self.rel_fixed_coord_hitbox_nose,
            delta_radians,
        )
        self.rel_rot_coord_hitbox_bottom_left = utils2d.rotate(
            constants.ORGIN_COORD,
            self.rel_fixed_coord_hitbox_bottom_left,
            delta_radians,
        )
        self.rel_rot_coord_hitbox_bottom_right = utils2d.rotate(
            constants.ORGIN_COORD,
            self.rel_fixed_coord_hitbox_bottom_right,
            delta_radians,
        )
