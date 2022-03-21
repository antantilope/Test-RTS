
""" Logging on the game server should be limited
        > if the server crashes we cant to log the traceback
"""

import datetime as dt
import logging
import os
from uuid import uuid4



LOG_FILE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "logs"
)

def get_log_file_path(level, name) -> str:
    now_ts = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(
        LOG_FILE_DIR,
        f"{now_ts}_LVL{level}_{name}_{uuid4().hex[:6]}.log"
    )

def get_logger(name: str):
    ISPYTESTING = os.getenv('ISPYTESTING') is not None

    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers = []

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    info_file = logging.FileHandler(get_log_file_path(logging.INFO, name), "a") if not ISPYTESTING else logging.NullHandler()
    info_file.setLevel(logging.INFO)
    info_file.setFormatter(formatter)
    logger.addHandler(info_file)

    warn_file = logging.FileHandler(get_log_file_path(logging.WARNING, name), "a") if not ISPYTESTING else logging.NullHandler()
    warn_file.setLevel(logging.WARNING)
    warn_file.setFormatter(formatter)
    logger.addHandler(warn_file)

    logger.info("logger instantiated")

    return logger
