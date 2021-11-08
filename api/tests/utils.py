
from api.models.ship import Ship

from typing import Callable, Optional
from decimal import Decimal



r = repr


TEST_ORIGIN = (100_000, 100_000,)

PROFILE_INCREASE = lambda delta: delta > 0
PROFILE_DECREASE = lambda delta: delta < 0
PROFILE_NO_CHANGE = lambda delta: delta == Decimal(delta).quantize(Decimal('0.0000')) == Decimal(0)


def assert_coord_in_quadrant(quadrant, point, origin=TEST_ORIGIN):
    if quadrant == 1:
        assert point[0] > TEST_ORIGIN[0] and point[1] > TEST_ORIGIN[1], f"point {point} not in quadrant {quadrant}"
    elif quadrant == 2:
        assert point[0] < TEST_ORIGIN[0] and point[1] > TEST_ORIGIN[1], f"point {point} not in quadrant {quadrant}"
    elif quadrant == 3:
        assert point[0] < TEST_ORIGIN[0] and point[1] < TEST_ORIGIN[1], f"point {point} not in quadrant {quadrant}"
    elif quadrant == 4:
        assert point[0] > TEST_ORIGIN[0] and point[1] < TEST_ORIGIN[1], f"point {point} not in quadrant {quadrant}"


def assert_floats_equal(f1: float, f2: float) -> bool:
    d1, d2 = Decimal(f1).quantize(Decimal('0.0000')), Decimal(f2).quantize(Decimal('0.0000'))
    assert d1 == d2, f"floats not equal. f1:{r(f1)} f2:{r(f2)} d1:{r(d1)} d2:{r(d2)}"


def assert_is_quadrant(quadrant: int):
    assert 1 <= quadrant <= 4, f"quadrant must be between 1 and 4, got {r(quadrant)}"


def assert_ship_moves_from_quadrant_to_quadrant(
    ship: "Ship",
    fps: int,
    start_quad: int,
    end_quad: int,
    x_velocity_profile: Optional[Callable] = None,
    y_velocity_profile: Optional[Callable] = None,
    max_frames=100,
):
    assert_is_quadrant(start_quad)
    assert_is_quadrant(end_quad)

    assert_coord_in_quadrant(start_quad, ship.coords)

    for _i in range(max_frames):

        old_x, old_y = ship.velocity_x_meters_per_second, ship.velocity_y_meters_per_second
        ship.calculate_physics(fps)
        new_x, new_y = ship.velocity_x_meters_per_second, ship.velocity_y_meters_per_second
        dx = new_x - old_x
        dy = new_y - old_y

        if x_velocity_profile is not None:
            if not x_velocity_profile(dx):
                raise AssertionError("x velocity profile assertion failed")

        if y_velocity_profile is not None:
            if not y_velocity_profile(dy):
                raise AssertionError("y velocity profile assertion failed")


        try:
            assert_coord_in_quadrant(end_quad, ship.coords)
        except AssertionError:
            pass
        else:
            return
        assert_coord_in_quadrant(start_quad, ship.coords)

    raise AssertionError(
        f"Expected ship to navigate to quadrant {end_quad}. After {max_frames} frames ship is not in quadrant {end_quad}."
    )


class DebugShip(Ship):

    def dprint(self, label: str, *args):
        print(label, *[r(v) for v in args])

    def print_physics_data(self):
        self.dprint("\n*****************\ndebug physics data for ship", r(self.id))
        self.dprint("MASS", self.mass)
        self.dprint("CORD X", self.coord_x)
        self.dprint("CORD Y", self.coord_y)
        self.dprint("HEADING", self.heading)
        self.dprint("VELOCITY X m/s", self.velocity_x_meters_per_second)
        self.dprint("VELOCITY Y m/s", self.velocity_y_meters_per_second)
        self.dprint('\nEND OF DEBUG\n*****************')
