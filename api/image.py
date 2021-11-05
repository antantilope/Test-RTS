"""

These functions are for development only
DO NOT call these functions within any game logic.

"""

import datetime as dt
import itertools
import os
import os.path
from typing import Optional, Tuple
import uuid

from cv2 import cv2
import numpy as np

from api.constants import (
    PIXEL_WHITE,
    CV2Color,
)



def get_filename_friendly_timestamp(now=None) -> str:
    nowts = now or dt.datetime.now()
    return nowts.strftime("%Y%m%d_%H%M%S")


def get_debug_image_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "debug_images"
    )


def get_debug_image_full_path(description: Optional[str] = None, ext: str = "jpg") -> str:
    dir_path = get_debug_image_dir()
    descr = description or 'debug_image'
    while True:
        uid = uuid.uuid4().hex[:6]
        timestamp = get_filename_friendly_timestamp()
        file_name = f"{descr}_{timestamp}_UID{uid}.{ext}"
        full_path = os.path.join(
            dir_path,
            file_name,
        )
        if not os.path.exists(full_path):
            return full_path
