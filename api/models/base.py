
import uuid


class BaseModel:
    def __init__(self, id=None):
        self.id = id or str(uuid.uuid4().hex)
