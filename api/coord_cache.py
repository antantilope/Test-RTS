
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union

from .utils2d import invert_heading


class BaseCoordCache(ABC):
    def __init__(self):
        self._data = {}

    def get_val(self, point_a: Tuple, point_b: Tuple) -> Optional[Union[int, float]]:
        key = (point_a, point_b,)
        if key in self._data:
            return self._data[key]

    @abstractmethod
    def set_val(self, point_a: Tuple, point_b: Tuple, val: Union[int, float]) -> None:
        ...


class CoordDistanceCache(BaseCoordCache):
    def set_val(self, point_a: Tuple, point_b: Tuple, val: Union[int, float]) -> None:
        self._data[(point_a, point_b,)] = val
        self._data[(point_b, point_a,)] = val


class CoordHeadingCache(BaseCoordCache):
    def set_val(self, point_a: Tuple, point_b: Tuple, val: Union[int, float]) -> None:
        self._data[(point_a, point_b,)] = val
        self._data[(point_b, point_a,)] = invert_heading(val)
