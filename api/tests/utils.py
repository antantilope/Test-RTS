
from api.models.ship import Ship

from decimal import Decimal


r = repr


def assert_floats_equal(f1: float, f2: float) -> bool:
    d1, d2 = Decimal(f1).quantize(Decimal('0.0000')), Decimal(f2).quantize(Decimal('0.0000'))
    r = repr
    assert d1 == d2, f"floats not equal. f1:{r(f1)} f2:{r(f2)} d1:{r(d1)} d2:{r(d2)}"




class DebugShip(Ship):

    def print_physics_data(self):
        print("\n*****************\ndebug physics data for ship", r(self.id))
        print("MASS", r(self.mass))
        print("CORD X", r(self.coord_x))
        print("CORD Y", r(self.coord_y))
        print("HEADING", r(self.heading))
        print("VELOCITY X m/s", r(self.velocity_x_meters_per_second))
        print("VELOCITY Y m/s", r(self.velocity_y_meters_per_second))
        print('\nEND OF DEBUG\n*****************')
