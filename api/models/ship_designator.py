
import random
from typing import Dict

def get_designations(ship_ids) -> Dict:

    part_1 = (
        'red', 'blue', 'green', 'pink', 'grey',
        'wild', 'lost', 'big', 'dusty', 'long',
        'little', 'old', 'bad', 'high', 'cold',
        'lucky', 'crazy', 'open', 'mad', 'wide', 'early',
    )
    part_2 = (
        'fox', 'dog', 'cat', 'fly', 'crow', 'pig',
        'eye', 'night', 'light', 'ranger', 'tale', 'rail',
        'flight', 'year', 'lake',
        'alpha', 'beta', 'gamma', 'delta', 'iota', 'lambda', 'omega', 'sigma',
    )

    if len(ship_ids) > len(part_1) or len(ship_ids) > len(part_2):
        raise Exception("too many ships to assign a unique identifier")

    shuffled_parts_1 = sorted(part_1, key=lambda v: random.random())
    shuffled_parts_2 = sorted(part_2, key=lambda v: random.random())

    out = {}
    parts = zip(shuffled_parts_1, shuffled_parts_2)
    for ship_id in ship_ids:
        parts_this_ship = next(parts)
        designator = f"{parts_this_ship[0]} {parts_this_ship[1]}"
        out[ship_id] = designator

    return out
