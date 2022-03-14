
import datetime as dt
import random
from typing import Tuple, TypedDict, Optional, List, Dict, Set
from time import sleep
import uuid
import re

from .base import BaseModel
from .ship import Ship, ShipScannerMode, ScannedElement, ScannedElementType,VisibleElementShapeType
from .ship_designator import get_designations
from api import utils2d
from api.constants import (
    MAX_SERVER_FPS,
    MIN_ELAPSED_TIME_PER_FRAME,
    GAME_START_COUNTDOWN_FROM,
)
from api.coord_cache import (
    CoordDistanceCache,
    CoordHeadingCache,
)
from api.logger import get_logger


LEADING_ZEROS_TIME = re.compile(r"^0+\:")


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
    team_id: str


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

        self.logger = get_logger("Game-Logger")

        self._players: Dict[str, PlayerDetails] = {}
        self._ships: Dict[str, Ship] = {}

        self._player_id_to_ship_id_map: Dict[str, str] = {}

        self._team_id_to_ship_id_map: Dict[str, str] = {}
        self._ship_id_to_team_id_map: Dict[str, str] = {}

        self._phase = GamePhase.LOBBY
        self._game_frame = 0
        self._max_players = 8
        self._game_start_countdown = GAME_START_COUNTDOWN_FROM

        self._map_units_per_meter = None
        self._map_x_unit_length = None
        self._map_y_unit_length = None

        self._fps = MAX_SERVER_FPS
        self._last_frame_at = None
        self._frame_sleep = None

        self._game_start_time = None


    def get_state(self) -> GameState:
        base_state = {
            'ok': True,
            'phase': self._phase,
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
            'elapsed_time': LEADING_ZEROS_TIME.sub("", str(dt.datetime.now() - self._game_start_time)).split(".")[0],
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
            team_id = self._players[player_id]['team_id']

            ship = Ship.spawn(
                team_id,
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

            self._team_id_to_ship_id_map[team_id] = ship.id
            self._ship_id_to_team_id_map[ship.id] = team_id

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
        self._game_start_time = dt.datetime.now()
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
            if self._game_frame != 1:
                raise Exception(
                    "Expected game_frame number to be 1 when _last_frame_at is None."
                )
            self._last_frame_at = now_ts
            self._fps = MAX_SERVER_FPS

        else:
            ellapsed_seconds = (now_ts - self._last_frame_at).total_seconds()
            fps = round(1 / ellapsed_seconds)

            if fps > MAX_SERVER_FPS:
                # Apply throttle
                diff = MIN_ELAPSED_TIME_PER_FRAME - ellapsed_seconds
                self._frame_sleep = diff
                sleep(diff)
                self._last_frame_at = dt.datetime.now() # Must set last_frame_at AFTER sleeping.
                self._fps = MAX_SERVER_FPS
            else:
                # No throttle needed
                self._frame_sleep = None
                self._fps = fps
                self._last_frame_at = now_ts

        if self._fps == 0:
            self.logger.warn("FPS set to 0, artificially adjusting to 1")
            self._fps = 1

        for ship_id, ship in self._ships.items():
            self._ships[ship_id].game_frame = self._game_frame

            # Reset thermal sig delta for this frame
            self._ships[ship_id].scanner_thermal_signature_delta = 0

            ship.adjust_resources(self._fps)
            ship.calculate_physics(self._fps)

            # calculate ship therm signature by subtracting
            delta_thermal = ship.scanner_thermal_signature_delta - (5 / self._fps)
            ship.scanner_thermal_signature = max(
                ship.scanner_thermal_signature + delta_thermal,
                0,
            )

        # Top Level side effects
        self.update_scanner_states()

        # Process user commands.
        for command in request['commands']:
            self._process_ship_command(command)

        # Weapons
        for ship_id, ship in self._ships.items():
            if ship.ebeam_firing:
                ship.use_ebeam_charge()
                line, hit = self.get_ebeam_line_and_hit(ship)


        self.incr_game_frame(self._fps)


    def get_ebeam_line_and_hit(self, ship: Ship) -> Tuple:
        # gets starting point of EBeam ray
        p0_x, p0_y = ship.map_p0
        p1_x, p1_y = ship.map_p1
        pm_x = round(p0_x + p1_x) / 2
        pm_y = round(p0_y + p1_y) / 2
        ship_on_line = utils2d.hitboxes_intercept_ray_factory((pm_x, pm_y), ship.heading)




    def update_scanner_states(self):
        distance_cache = CoordDistanceCache()
        heading_cache = CoordHeadingCache()

        for ship_id in self._ships:
            self._ships[ship_id].scanner_data.clear()

            scan_range = self._ships[ship_id].scanner_range if self._ships[ship_id].scanner_online else None
            visual_range = self._ships[ship_id].visual_range

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

                is_visual = visual_range >= distance_meters
                is_scannable = scan_range is not None and scan_range >= distance_meters
                if not is_scannable and not is_visual:
                    continue

                scan_only = is_scannable and not is_visual
                if (
                    scan_only
                    and self._ships[ship_id].scanner_mode == ShipScannerMode.IR
                    and not (
                        self._ships[other_id].scanner_thermal_signature
                        >= self._ships[ship_id].scanner_ir_minimum_thermal_signature)
                ):
                    is_scannable = False

                if(
                    scan_only
                    and self._ships[ship_id].scanner_mode == ShipScannerMode.RADAR
                    and (
                        self._ships[other_id].anti_radar_coating_level
                        > self._ships[ship_id].scanner_radar_sensitivity)
                ):
                    is_scannable = False

                if is_visual or is_scannable:
                    scanner_data: ScannedElement = {
                        'id': other_id,
                        'designator': self._ships[other_id].scanner_designator,
                        'coord_x': other_coords[0],
                        'coord_y': other_coords[1],
                        'element_type': ScannedElementType.SHIP,
                    }
                    if is_visual:
                        scanner_data.update({
                            'visual_shape': VisibleElementShapeType.RECT,
                            'visual_p0': self._ships[other_id].map_p0,
                            'visual_p1': self._ships[other_id].map_p1,
                            'visual_p2': self._ships[other_id].map_p2,
                            'visual_p3': self._ships[other_id].map_p3,
                            'visual_fin_0_rel_rot_coord_0': self._ships[other_id].map_fin_0_coord_0,
                            'visual_fin_0_rel_rot_coord_1': self._ships[other_id].map_fin_0_coord_1,
                            'visual_fin_1_rel_rot_coord_0': self._ships[other_id].map_fin_1_coord_0,
                            'visual_fin_1_rel_rot_coord_1': self._ships[other_id].map_fin_1_coord_1,
                            'visual_engine_lit': self._ships[other_id].engine_lit,
                            'visual_ebeam_charging': self._ships[other_id].ebeam_charging,
                            'visual_ebeam_firing': self._ships[other_id].ebeam_firing,
                            'visual_fill_color': '#ffffff',
                        })
                    if is_scannable:
                        heading = heading_cache.get_val(ship_coords, other_coords)
                        if heading is None:
                            heading = round(utils2d.calculate_heading_to_point(ship_coords, other_coords))
                            heading_cache.set_val(ship_coords, other_coords, heading)
                        scanner_data['distance'] = round(distance_meters)
                        scanner_data['relative_heading'] = heading
                        if self._ships[ship_id].scanner_mode == ShipScannerMode.IR:
                            scanner_data['thermal_signature'] = self._ships[other_id].scanner_thermal_signature

                    self._ships[ship_id].scanner_data[other_id] = scanner_data


            if self._ships[ship_id].scanner_lock_target and self._ships[ship_id].scanner_lock_target not in self._ships[ship_id].scanner_data:
                if self._ships[ship_id].scanner_locking:
                    self._ships[ship_id].scanner_lock_target = None
                    self._ships[ship_id].scanner_locking = False
                    self._ships[ship_id].scanner_locking_power_used = None
                elif self._ships[ship_id].scanner_locked:
                    self._ships[ship_id].scanner_lock_target = None
                    self._ships[ship_id].scanner_locked = False


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

