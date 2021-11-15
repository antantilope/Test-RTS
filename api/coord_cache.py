
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple

from .utils2d import invert_heading


class BaseCoordCache(ABC):
    def __init__(self):
        self._data = {}

    def get_val(self, point_a: Tuple, point_b: Tuple) -> Optional[Any]:
        key = (point_a, point_b,)
        if key in self._data:
            return self._data[key]

    @abstractmethod
    def set_val(self, point_a: Tuple, point_b: Tuple, val: Any) -> None:
        ...


class CoordDistanceCache(BaseCoordCache):
    def set_val(self, point_a: Tuple, point_b: Tuple, val: Any) -> None:
        self._data[(point_a, point_b,)] = val
        self._data[(point_b, point_a,)] = val


class CoordHeadingCache(BaseCoordCache):
    def set_val(self, point_a: Tuple, point_b: Tuple, val: Any) -> None:
        self._data[(point_a, point_b,)] = val
        self._data[(point_b, point_a,)] = invert_heading(val)
