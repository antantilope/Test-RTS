
import random
from typing import Dict
def get_designations(ship_ids) -> Dict:
    part_1 = (
        'red', 'blue', 'green', 'pink', 'grey',
        'wild', 'lost', 'big', 'dusty', 'long',
        'spicy', 'foul', 'great', 'dirty', 'bare',
        'little', 'old', 'bad', 'high', 'cold',
        'lucky', 'crazy', 'open', 'mad', 'wide',
        'full', 'busy', 'grim', 'half', 'holy',
        'lone', 'pale', 'tall', 'real', 'sick',
        'true',
    )
    part_2 = (
        'fox', 'dog', 'cat', 'fly', 'crow',
        'pig', 'hare', 'eye', 'night', 'light',
        'ranger', 'tale', 'rail', 'flight', 'year',
        'lake', 'metal', 'bone', 'love', 'alpha',
        'beta', 'gamma', 'delta', 'iota', 'lambda',
        'omega', 'sigma', 'echo', 'kilo', 'bank',
        'path', 'rock', 'side', 'site', 'show',
    )
    if len(part_1) != len(set(part_1)):
        raise Exception("duplicate part_1")
    if len(part_2) != len(set(part_2)):
        raise Exception("duplicate part_1")
    if any(len(w) > 6 for w in part_1):
        raise Exception("part_1 word too long")
    if any(len(w) > 6 for w in part_2):
        raise Exception("part_2 word too long")
    if len(ship_ids) > len(part_1) or len(ship_ids) > len(part_2):
        raise Exception("too many ships to assign a unique identifier")
    shuffled_parts_1 = sorted(part_1, key=lambda v: random.random())
    shuffled_parts_2 = sorted(part_2, key=lambda v: random.random())
    out = {}
    parts = zip(shuffled_parts_1, shuffled_parts_2)
    for ship_id in ship_ids:
        while True:
            parts_this_ship = next(parts)
            designator = f"{parts_this_ship[0]} {parts_this_ship[1]}"
            if len(designator) > 10:
                continue
            else:
                break
        out[ship_id] = designator
    return out
