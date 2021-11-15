
from typing import Any, Optional, Tuple

from .utils2d import invert_heading


class BaseCoordCache:
    def __init__(self):
        self._data = {}


class CoordDistanceCache(BaseCoordCache):
    def get_val(self, point_a: Tuple, point_b: Tuple) -> Optional[Any]:
        key1 = (point_a, point_b,)
        if key1 in self._data:
            return self._data[key1]
        key2 = (point_b, point_a,)
        if key2 in self._data:
            return self._data[key2]

    def set_val(self, point_a, point_b, val) -> None:
        self._data[(point_a, point_b,)] = val
        self._data[(point_b, point_a,)] = val


class CoordHeadingCache(BaseCoordCache):
    def get_val(self, point_a: Tuple, point_b: Tuple) -> Optional[Any]:
        key1 = (point_a, point_b,)
        if key1 in self._data:
            return self._data[key1]
        key2 = (point_b, point_a,)
        if key2 in self._data:
            return self._data[key2]

    def set_val(self, point_a, point_b, val)-> None:
        self._data[(point_a, point_b,)] = val
        self._data[(point_b, point_a,)] = invert_heading(val)
