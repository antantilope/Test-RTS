

from api.models.base import BaseModel



class MagnetMine(BaseModel):

    def __init__(self, game_frame: int, ship_id: str):
        super().__init__()
        self.elapsed_milliseconds = 0
        self.created_frame = game_frame
        self.ship_id = ship_id

        self.armed = False
        self.percent_armed = 0
        self.exploded = False

        # Position
        self.coord_x = 0
        self.coord_y = 0

        # Velocity
        self.velocity_x_meters_per_second = float(0)
        self.velocity_y_meters_per_second = float(0)

        self.closest_ship_id = None
        self.distance_to_closest_ship = None

    @property
    def coords(self):
        return (self.coord_x, self.coord_y,)
