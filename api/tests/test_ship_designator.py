
from uuid import uuid4
from unittest import TestCase

from api.models.ship_designator import get_designations


class TestGetDesignations(TestCase):
    def test_get_unique_list_of_designations(self):
        id1 = str(uuid4())
        id2 = str(uuid4())
        id3 = str(uuid4())

        designations = get_designations([id1, id2, id3])
        assert isinstance(designations, dict)
        assert len(designations) == 3
        assert len(set(designations.values())) == 3
        assert all(len(v.split(" ")) == 2 for v in designations.values())
