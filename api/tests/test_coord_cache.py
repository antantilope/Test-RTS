
from unittest import TestCase

from api.coord_cache import (
    CoordDistanceCache,
    CoordHeadingCache,
)


class TestCoordDistanceCache(TestCase):
    def test_can_set_cache_distance_value(self):
        cache = CoordDistanceCache()
        point_a = (1, 2)
        point_b = (1, 10)
        distance = 8
        cache.set_val(point_a, point_b)
        assert cache._data == {
            (point_a, point_b): distance,
            (point_b, point_a): distance,
        }

    def test_can_read_cache_distance_value(self):
        cache = CoordDistanceCache()
        point_a = (1, 2)
        point_b = (1, 10)
        distance = 8

        assert cache.get_val(point_a, point_b) == distance
        assert cache.get_val(point_b, point_a) == distance



class TestCoordHeadingCache(TestCase):
    def test_can_set_cache_heading_value(self):
        cache = CoordHeadingCache()
        point_a = (-5, 5)
        point_b = (5, -5)
        heading_a_to_b = 135
        heading_b_to_a = 315
        cache.set_val(point_a, point_b)
        assert cache._data == {
            (point_a, point_b): heading_a_to_b, # A to B is cached
            (point_b, point_a): heading_b_to_a, # B to A is calculated and cached.
        }

    def test_can_read_cache_heading_value(self):
        cache = CoordHeadingCache()
        point_a = (-5, 5)
        point_b = (5, -5)
        heading_a_to_b = 135
        heading_b_to_a = 315
        cache.set_val(point_a, point_b)

        assert cache.get_val(point_a, point_b) == heading_a_to_b
        assert cache.get_val(point_b, point_a) == heading_b_to_a
