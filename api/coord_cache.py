
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union

from .utils2d import invert_heading, calculate_point_distance, calculate_heading_to_point


class BaseCoordCache(ABC):
    def __init__(self):
        self._data = {}

    def clear(self):
        self._data.clear()

    def get_val(self, point_a: Tuple, point_b: Tuple) -> Optional[Union[int, float]]:
        key = (point_a, point_b,)
        if key in self._data:
            return self._data[key]
        return self.set_val(point_a, point_b)

    @abstractmethod
    def set_val(self, point_a: Tuple, point_b: Tuple):
        ...


class CoordDistanceCache(BaseCoordCache):
    def set_val(self, point_a: Tuple, point_b: Tuple):
        val = calculate_point_distance(point_a, point_b)
        self._data[(point_a, point_b,)] = val
        self._data[(point_b, point_a,)] = val
        return val


class CoordHeadingCache(BaseCoordCache):
    def set_val(self, point_a: Tuple, point_b: Tuple):
        val = calculate_heading_to_point(point_a, point_b)
        self._data[(point_a, point_b,)] = val
        self._data[(point_b, point_a,)] = invert_heading(val)
        return val
