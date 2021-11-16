
import datetime as dt
import random
from typing import TypedDict, Optional, List, Dict, Set
from time import sleep
import uuid

from .base import BaseModel
from .ship import Ship, ShipScannerMode
from .ship_designator import get_designations
from api import utils2d
from api.constants import (
    MAX_SERVER_FPS,
    MIN_ELAPSED_TIME_PER_FRAME,
)
from api.coord_cache import (
    CoordDistanceCache,
    CoordHeadingCache,
)


class GameError(Exception): pass


class GamePhase:
    LOBBY = '0-lobby'
    STARTING = '1-starting'
    LIVE = '2-live'
    COMPLETE = '3-complete'

    NON_LOBBY_PHASES = (STARTING, LIVE, COMPLETE, )


class PlayerDetails(TypedDict):
    player_name: str
    player_id: str


class MapConfigDetails(TypedDict):
    units_per_meter: int
    x_unit_length: int
    y_unit_length: int


class GameState(TypedDict):
    phase: str
    game_frame: Optional[int]
    players: List[PlayerDetails]
    map_config: MapConfigDetails
    game_start_countdown: Optional[int]
    ships: Optional[List]


class FrameCommand(TypedDict):
    player_id: str
    ship_command: str
    args: Optional[List]
    kwargs: Optional[Dict]


class RunFrameDetails(TypedDict):
    commands: List[FrameCommand]


class Game(BaseModel):

    BASE_STATE_KEYS = ('ok', 'phase', 'map_config', 'players', 'map_config',)

    def __init__(self):
        super().__init__()

        self._players: Dict[str, PlayerDetails] = {}
        self._ships: Dict[str, Ship] = {}
        self._player_id_to_ship_id_map: Dict[str, str] = {}

        self._phase = GamePhase.LOBBY
        self._game_frame = 0
        self._max_players = 8
        self._game_start_countdown = 5

        self._map_units_per_meter = None
        self._map_x_unit_length = None
        self._map_y_unit_length = None

        self._fps = 24
        self._last_frame_at = None
        self._frame_sleep = None


    def get_state(self) -> GameState:
        base_state = {
            'ok': True,
            'phase': self._phase if self._game_frame < 10 else GamePhase.COMPLETE,
            'game_frame': self._game_frame,
            'players': self._players,
            'server_fps': self._fps,
            'server_fps_throttle_seconds': self._frame_sleep,
            'map_config': {
                "units_per_meter": self._map_units_per_meter,
                "x_unit_length": self._map_x_unit_length,
                "y_unit_length": self._map_y_unit_length,
            }
        }

        if self._phase == GamePhase.LIVE:
            return {
                **base_state,
                **self._get_live_state(),
            }

        elif self._phase == GamePhase.LOBBY:
            return base_state

        elif self._phase == GamePhase.STARTING:
            return {
                **base_state,
                'game_start_countdown': self._game_start_countdown,
            }

        elif self._phase == GamePhase.COMPLETE:
            pass

        raise NotImplementedError


    def _get_live_state(self) -> Dict:
        return {
            'ships': [ship.to_dict() for ship in self._ships.values()],
        }


    # Phase 0 # #
    def register_player(self, request: PlayerDetails):
        self._validate_can_add_player(request['player_id'])
        self._players[request['player_id']] = request

    def remove_player(self, player_id: str):
        try:
            self._players.pop(player_id)
        except KeyError as e:
            print("could not delete player, KeyError, player_id ", player_id, e)
            pass

    def _validate_can_add_player(self, player_id: str):
        if self._phase != GamePhase.LOBBY:
            raise GameError("Cannot add player during this phase")
        if player_id in self._players:
            raise GameError("Player is already registered")
        if len(self._players) >= self._max_players:
            raise GameError("Maximum players in game")


    def configure_map(self, request: MapConfigDetails):
        self._validate_can_configure_map(request)
        self._map_units_per_meter = request['units_per_meter']
        self._map_x_unit_length = request['x_unit_length']
        self._map_y_unit_length = request['y_unit_length']


    def _validate_can_configure_map(self, request: MapConfigDetails):
        if self._phase != GamePhase.LOBBY:
            raise GameError("Cannot configure map during this phase")


    @property
    def map_is_configured(self) -> bool:
        return (
            self._map_units_per_meter is not None
            and self._map_x_unit_length is not None
            and self._map_y_unit_length is not None
        )


    def advance_to_phase_1_starting(self):
        self._validate_can_advance_to_phase_1_starting()
        self._phase = GamePhase.STARTING
        self._spawn_ships()

        for ship_id, designator in get_designations(list(self._ships.keys())).items():
            self._ships[ship_id].scanner_designator = designator


    def _validate_can_advance_to_phase_1_starting(self):
        if self._phase != GamePhase.LOBBY:
            raise GameError("Cannot advance to phase 1 starting unless in phase 0 lobby")
        if len(self._players) < 2:
            raise GameError("Not enough players registered")
        if not self.map_is_configured:
            raise GameError("Map must be configued to advance to phase 1")


    # Phase 1 # #
    def _spawn_ships(self):
        """ TODO: Check for even spacing, add min_spacing value.
        """
        placed_points = []
        for player_id in self._players.keys():
            ship = Ship.spawn(
                map_units_per_meter=self._map_units_per_meter
            )

            placement_buffer = (self._map_units_per_meter * 100)
            x_min = abs(ship.h0_x1) + placement_buffer
            y_min = abs(ship.h0_y1) + placement_buffer
            x_max = self._map_x_unit_length - abs(ship.h0_x1) - placement_buffer
            y_max = self._map_y_unit_length - abs(ship.h0_y1) - placement_buffer
            coord_x = random.randint(x_min, x_max)
            coord_y = random.randint(y_min, y_max)
            ship.coord_x = coord_x
            ship.coord_y = coord_y

            self._player_id_to_ship_id_map[player_id] = ship.id
            self._ships[ship.id] = ship


    def decr_phase_1_starting_countdown(self):
        self._validate_can_decr_phase_1_starting_countdown()
        self._game_start_countdown -= 1
        if self._game_start_countdown == 0:
            self.advance_to_phase_2_live()


    def _validate_can_decr_phase_1_starting_countdown(self):
        if self._phase != GamePhase.STARTING:
            raise GameError("Cannot decr game start countdown outside phase 1 starting")
        if self._game_start_countdown == 0:
            raise GameError("Cannot decr game start countdown, countdown at 0")


    def advance_to_phase_2_live(self):
        self._validate_advance_to_phase_2_live()
        self._phase = GamePhase.LIVE
        self.incr_game_frame()

    def incr_game_frame(self):
        self._game_frame += 1

    def _validate_advance_to_phase_2_live(self):
        if self._game_start_countdown != 0:
            raise GameError("Cannot advance to phase 2 live, game start countdown not yet exhausted.")
        if self._phase != GamePhase.STARTING:
            raise GameError("Cannot advance to phase 2 live unless in phase 1 starting")


    def run_frame(self, request: RunFrameDetails):
        """ Run frame phases and increment game frame number.
        """

        # Calculate Frame Per Second, throttle with sleep command if FPS is too high
        now_ts = dt.datetime.now()
        if self._last_frame_at is None:
            self._last_frame_at = now_ts
        else:
            ellapsed_seconds = (now_ts - self._last_frame_at).total_seconds()
            fps = round(1 / ellapsed_seconds)

            if fps > MAX_SERVER_FPS:
                # Apply throttle
                diff = MIN_ELAPSED_TIME_PER_FRAME - ellapsed_seconds
                self._frame_sleep = diff
                sleep(diff)
                self._last_frame_at = dt.datetime.now()
                self._fps = MAX_SERVER_FPS
            else:
                # No throttle needed
                self._frame_sleep = None
                self._fps = fps
                self._last_frame_at = now_ts

        # Run Frame Phases
        for ship_id, ship in self._ships.items():
            self._ships[ship_id].game_frame = self._game_frame

            # Phase 0
            ship.calculate_damage()
            # Phase 1
            ship.adjust_resources()
            # Phase 2
            ship.calculate_physics(self._fps)
            # Phase 3
            ship.calculate_side_effects()


        # Phase 3 (again): Top Level side effects
        self.update_scanner_states()

        # Phase 4
        for command in request['commands']:
            self._process_ship_command(command)

        self.incr_game_frame()


    def update_scanner_states(self):
        distance_cache = CoordDistanceCache()
        heading_cache = CoordHeadingCache()

        for ship_id in self._ships:
            self._ships[ship_id].scanner_data.clear()

            if not self._ships[ship_id].scanner_online:
                continue

            scan_range = self._ships[ship_id].scanner_range

            for other_id in self._ships:
                if other_id == ship_id:
                    continue

                other_coords = self._ships[other_id].coords
                ship_coords = self._ships[ship_id].coords

                distance = distance_cache.get_val(ship_coords, other_coords)
                if distance is None:
                    distance = utils2d.calculate_point_distance(ship_coords, other_coords)
                    distance_cache.set_val(ship_coords, other_coords, distance)
                distance_meters = round(distance / self._map_units_per_meter)

                if scan_range >= distance_meters:
                    heading = heading_cache.get_val(ship_coords, other_coords)
                    if heading is None:
                        heading = round(utils2d.calculate_heading_to_point(ship_coords, other_coords))
                        heading_cache.set_val(ship_coords, other_coords, heading)

                    if self._ships[ship_id].scanner_mode == ShipScannerMode.RADAR:
                        self._ships[ship_id].scanner_data[other_id] = {
                            'designator': self._ships[other_id].scanner_designator,
                            'diameter_meters': self._ships[other_id].scanner_diameter,
                            'coord_x': other_coords[0],
                            'coord_y': other_coords[1],
                            'distance': round(distance_meters),
                            'relative_heading': heading,
                        }
                    elif self._ships[ship_id].scanner_mode == ShipScannerMode.IR:
                        if (
                            self._ships[other_id].scanner_thermal_signature
                            >= self._ships[ship_id].scanner_ir_minimum_thermal_signature
                        ):
                            self._ships[ship_id].scanner_data[other_id] = {
                                'designator': self._ships[other_id].scanner_designator,
                                'thermal_signature': self._ships[other_id].scanner_thermal_signature,
                                'coord_x': other_coords[0],
                                'coord_y': other_coords[1],
                                'distance': round(distance_meters),
                                'relative_heading': heading,
                            }
                    else:
                        raise NotImplementedError


    def _process_ship_command(self, command: FrameCommand):
        ship_command = command['ship_command']
        player_id = command['player_id']
        args = command.get('args', [])
        kwargs = command.get('kwargs', {})
        ship_id = self._player_id_to_ship_id_map[player_id]

        self._ships[ship_id].process_command(
            ship_command,
            *args,
            **kwargs,
        )

