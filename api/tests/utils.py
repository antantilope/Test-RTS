
from api.models.ship import Ship

from decimal import Decimal


r = repr


def assert_floats_equal(f1: float, f2: float) -> bool:
    d1, d2 = Decimal(f1).quantize(Decimal('0.0000')), Decimal(f2).quantize(Decimal('0.0000'))
    assert d1 == d2, f"floats not equal. f1:{r(f1)} f2:{r(f2)} d1:{r(d1)} d2:{r(d2)}"


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
