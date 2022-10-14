
from collections import OrderedDict
import json
import datetime as dt
from typing import Tuple, TypedDict, Optional, List, Dict
from time import sleep
import re
import traceback
from uuid import uuid4

from api import constants

from .base import BaseModel
from .ship import (
    Ship,
    ShipCommands,
    ShipDeathType,
    ShipScannerMode,
    ScannedElement,
    ScannedElementType,
    VisibleElementShapeType,
    MapMiningLocationDetails,
    MapSpaceStation,
    AutopilotError,
)
from .ship_designator import get_designations
from api import utils2d
from api.constants import (
    MAX_SERVER_FPS,
    MIN_ELAPSED_TIME_PER_FRAME,
    GAME_START_COUNTDOWN_FROM,
    FINAL_EXPLOSION_FRAME,
)
from api.coord_cache import (
    CoordDistanceCache,
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
    map_name: str


class TopLevelMapDetails(TypedDict):
    name: str
    meters_x: int
    meters_y: int


class MapFeature(TypedDict):
    id: str
    name: Optional[str]
    position_meters_x: int
    position_meters_y: int
    width_meters_x: int
    width_meters_y: int
    type: str

class MapSpawnPoint(TypedDict):
    id: str
    position_meters_x: int
    position_meters_y: int

class MapDetails(TypedDict):
    mapData: TopLevelMapDetails
    features: List[MapFeature]
    spawnPoints: List[MapSpawnPoint]

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


class EBeamRayDetails(TypedDict):
    start_point: Tuple[int]
    end_point: Tuple[int]
    color: str

class KillFeedElement(TypedDict):
    victim_name: str
    created_at_frame: int

class ExplosionShockwave(TypedDict):
    id: str
    origin_point: Tuple[int]
    radius_meters: int

class Game(BaseModel):

    BASE_STATE_KEYS = ('ok', 'phase', 'map_config', 'players',)

    def __init__(self):
        super().__init__()

        self.logger = get_logger("Game-Logger")

        self._spawn_points: List[MapSpawnPoint] = []

        self._players: Dict[str, PlayerDetails] = {}
        self._ships: Dict[str, Ship] = OrderedDict()
        self._ebeam_rays: List[EBeamRayDetails] = []
        self._killfeed: List[KillFeedElement] = []
        self._explosion_shockwaves: List[ExplosionShockwave] = []
        self._explosion_shockwave_max_radius_meters = None
        self._space_stations: List[MapSpaceStation] = []
        self._ore_mines: List[MapMiningLocationDetails] = []
        self._ore_mines_remaining_ore: Dict[str, float] = {}


        self._player_id_to_ship_id_map: Dict[str, str] = {}

        self._team_id_to_ship_id_map: Dict[str, str] = {}
        self._ship_id_to_team_id_map: Dict[str, str] = {}

        self._phase = GamePhase.LOBBY
        self._game_frame = 0
        self._max_players = 8
        self._game_start_countdown = GAME_START_COUNTDOWN_FROM
        self._winning_team = None

        self._map_units_per_meter = None
        self._map_x_unit_length = None
        self._map_y_unit_length = None
        self._map_name = None

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
                "map_name": self._map_name,
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
            return base_state

        raise NotImplementedError


    def _get_live_state(self) -> Dict:
        return {
            'elapsed_time': LEADING_ZEROS_TIME.sub("", str(dt.datetime.now() - self._game_start_time)).split(".")[0],
            'ships': [ship.to_dict() for ship in self._ships.values()],
            'ebeam_rays': self._ebeam_rays,
            'explosion_shockwaves': self._explosion_shockwaves,
            "winning_team": self._winning_team,
            "killfeed": self._killfeed,
            "space_stations": self._space_stations,
            "ore_mines": self._ore_mines,
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


    def set_map(self, request: MapDetails, map_units_per_meter = None):
        self._validate_can_set_map()

        self._map_units_per_meter = map_units_per_meter or 100
        self._map_x_unit_length = request['mapData']['meters_x'] * self._map_units_per_meter
        self._map_y_unit_length = request['mapData']['meters_y'] * self._map_units_per_meter
        self._map_name = request['mapData']['name']
        self._spawn_points = request['spawnPoints']
        self._space_stations = [
            {
               "position_map_units_x": f['position_meters_x'] * self._map_units_per_meter,
               "position_map_units_y": f['position_meters_y'] * self._map_units_per_meter,
               "service_radius_map_units": f['service_radius_meters'] * self._map_units_per_meter,
                **f,
            }
            for f in request['spaceStations']
        ]
        self._ore_mines = [
            {
                "position_map_units_x": f['position_meters_x'] * self._map_units_per_meter,
                "position_map_units_y": f['position_meters_y'] * self._map_units_per_meter,
                "service_radius_map_units": f['service_radius_meters'] * self._map_units_per_meter,
                **f,
            }
            for f in request['miningLocations']
        ]
        for om in self._ore_mines:
            self._ore_mines_remaining_ore[om['uuid']] = om['starting_ore_amount_kg']

        self._explosion_shockwave_max_radius_meters = max(
            request['mapData']['meters_x'],
            request['mapData']['meters_y'],
        )

    def _validate_can_set_map(self):
        if self._phase != GamePhase.LOBBY:
            raise GameError("Cannot configure map during this phase")

        if self._map_units_per_meter:
            raise GameError("map units per meter already set")

        if self._spawn_points:
            raise GameError("Spawn points already set")

        if self._ore_mines:
            raise GameError("Ore mines already set")

        if self._space_stations:
            raise GameError("space stations already set")

    @property
    def map_is_configured(self) -> bool:
        return (
            self._map_units_per_meter is not None
            and self._map_x_unit_length is not None
            and self._map_y_unit_length is not None
            and len(self._spawn_points) > 0
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
        for ix, player_id in enumerate(self._players.keys()):
            team_id = self._players[player_id]['team_id']

            ship = Ship.spawn(
                team_id,
                map_units_per_meter=self._map_units_per_meter
            )

            coord_x = self._spawn_points[ix]['position_meters_x'] * self._map_units_per_meter
            coord_y = self._spawn_points[ix]['position_meters_y'] * self._map_units_per_meter
            ship.coord_x = coord_x
            ship.coord_y = coord_y

            self._player_id_to_ship_id_map[player_id] = ship.id

            self._team_id_to_ship_id_map[team_id] = ship.id
            self._ship_id_to_team_id_map[ship.id] = team_id

            self._ships[ship.id] = ship

            # initialize scouted ore values
            for om in self._ore_mines:
                self._ships[ship.id].scouted_mine_ore_remaining[
                    om['uuid']
                ] = om['starting_ore_amount_kg']

            # initialize cached map data
            self._ships[ship.id]._ore_mines = {
                om['uuid']: om for om in self._ore_mines
            }
            self._ships[ship.id]._space_stations = {
                st['uuid']: st for st in self._space_stations
            }

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

        # Process user commands.
        for command in request['commands']:
            try:
                self._process_ship_command(command)
            except Exception as e:
                self.logger.error("error running ship command")
                self.logger.error(json.dumps(command))
                tb = traceback.format_exc()
                self.logger.error(tb)

        self._ebeam_rays.clear()
        check_for_gravity_brake_catches = self._game_frame % 4 == 0
        check_for_ore_mine_parking = self._game_frame % 60 == 0

        for ship_id, ship in self._ships.items():
            ship.advance_upgrades(self._fps)
            ship.advance_gravity_brake_position(self._fps)
            ship.adjust_resources(self._fps, self._game_frame)
            ship.calculate_physics(self._fps)
            ship.advance_thermal_signature(self._fps)
            self.reset_and_update_scanner_states(ship_id)

            # Autopilot/weapons updates must run after scanner/physics updates
            try:
                ship.run_autopilot()
            except AutopilotError as e:
                self.logger.error(f"autopilot error (ship {ship_id}) {e}")
            self.calculate_weapons_and_damage(ship_id)

            if check_for_gravity_brake_catches:
                self.check_for_gravity_brake_catch(ship_id)

            if check_for_ore_mine_parking:
                self.check_for_ore_mine_parking(ship_id)
                self.update_scouted_mine_ore_remaining(ship_id)

            self.advance_mining(ship_id)

        if any(self._explosion_shockwaves):
            self.advance_explosion_shockwaves()

        # Post frame checks
        if self._game_frame % 45 == 0:
            if not self._winning_team:
                self.check_for_winning_team()
            self.check_for_empty_game()
            self.purge_killfeed(MAX_SERVER_FPS)

        # Increment the game frame for the next frame.
        self.incr_game_frame()


    def advance_explosion_shockwaves(self):
        delta_radius = constants.SPEED_OF_SOUND_METERS_PER_SECOND / self._fps
        ix_to_remove = set()
        for ix, esw in enumerate(self._explosion_shockwaves):
            new_radius = esw['radius_meters'] + delta_radius
            if new_radius > self._explosion_shockwave_max_radius_meters:
                ix_to_remove.add(ix)
            else:
                self._explosion_shockwaves[ix]['radius_meters'] = new_radius

        if ix_to_remove:
            self._explosion_shockwaves = [
                esw
                for ix, esw in enumerate(self._explosion_shockwaves)
                if ix not in ix_to_remove
            ]

    def reset_and_update_scanner_states(self, ship_id: str):
        distance_cache = CoordDistanceCache()

        self._ships[ship_id].scanner_data.clear()

        scan_range = self._ships[ship_id].scanner_range if self._ships[ship_id].scanner_online else None
        visual_range = self._ships[ship_id].visual_range

        for other_id in (v for v in self._ships if v != ship_id):

            if self._ships[other_id].explosion_frame and self._ships[other_id].explosion_frame > FINAL_EXPLOSION_FRAME:
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
                exact_heading = utils2d.calculate_heading_to_point(ship_coords, other_coords)
                scanner_data: ScannedElement = {
                    'id': other_id,
                    'designator': self._ships[other_id].scanner_designator,
                    'anti_radar_coating_level': self._ships[other_id].anti_radar_coating_level,
                    'scanner_thermal_signature': self._ships[other_id].scanner_thermal_signature,
                    'coord_x': other_coords[0],
                    'coord_y': other_coords[1],
                    'element_type': ScannedElementType.SHIP,
                    'alive': self._ships[other_id].died_on_frame is None,
                    'aflame': self._ships[other_id].aflame_since_frame is not None,
                    'explosion_frame': self._ships[other_id].explosion_frame,
                    'in_visual_range': is_visual,
                    'visual_p0': self._ships[other_id].map_p0,
                    'visual_p1': self._ships[other_id].map_p1,
                    'visual_p2': self._ships[other_id].map_p2,
                    'visual_p3': self._ships[other_id].map_p3,
                    'visual_ebeam_charging': self._ships[other_id].ebeam_charging,
                    'visual_shape': VisibleElementShapeType.RECT,
                    'visual_fin_0_rel_rot_coord_0': self._ships[other_id].map_fin_0_coord_0,
                    'visual_fin_0_rel_rot_coord_1': self._ships[other_id].map_fin_0_coord_1,
                    'visual_fin_1_rel_rot_coord_0': self._ships[other_id].map_fin_1_coord_0,
                    'visual_fin_1_rel_rot_coord_1': self._ships[other_id].map_fin_1_coord_1,
                    'visual_engine_lit': self._ships[other_id].engine_lit,
                    'visual_engine_boosted_last_frame': self._ships[other_id].engine_boosted_last_frame,
                    'visual_ebeam_firing': self._ships[other_id].ebeam_firing,
                    'visual_ebeam_color': self._ships[other_id].ebeam_color,
                    'visual_fill_color': '#ffffff',
                    'visual_gravity_brake_position': self._ships[other_id].gravity_brake_position,
                    'visual_gravity_brake_deployed_position': self._ships[other_id].gravity_brake_deployed_position,
                    'visual_gravity_brake_active': self._ships[other_id].gravity_brake_active,
                    'visual_mining_ore_location': (
                        self._ships[other_id].parked_at_ore_mine
                        if self._ships[other_id].mining_ore
                        else None
                    ),
                    'visual_fueling_at_station': self._ships[other_id].fueling_at_station,
                    "distance": round(distance_meters),
                    "relative_heading": round(exact_heading),
                    "target_heading": exact_heading,
                }

                self._ships[ship_id].scanner_data[other_id] = scanner_data

        # Check if scanner target has gone out of range
        if self._ships[ship_id].scanner_lock_target and self._ships[ship_id].scanner_lock_target not in self._ships[ship_id].scanner_data:
            self._ships[ship_id].scanner_lock_traversal_slack = None
            self._ships[ship_id].scanner_lock_target = None
            if self._ships[ship_id].scanner_locking:
                self._ships[ship_id].scanner_locking = False
                self._ships[ship_id].scanner_locking_power_used = None
            elif self._ships[ship_id].scanner_locked:
                self._ships[ship_id].scanner_locked = False

        # check if scanner target traversal is above maximum
        if self._ships[ship_id].scanner_lock_target and (self._ships[ship_id].scanner_locking or self._ships[ship_id].scanner_locked):
            if self._ships[ship_id].scanner_lock_traversal_degrees_previous_frame is None:
                self._ships[ship_id].scanner_lock_traversal_degrees_previous_frame = self._ships[ship_id].scanner_data[
                    self._ships[ship_id].scanner_lock_target
                ]['target_heading']
            else:
                target_heading = self._ships[ship_id].scanner_data[
                    self._ships[ship_id].scanner_lock_target
                ]['target_heading']
                delta = abs(
                    self._ships[ship_id].scanner_lock_traversal_degrees_previous_frame
                    - target_heading
                )
                if self._ships[ship_id].scanner_locking:
                    max_traversal = self._ships[ship_id].scanner_locking_max_traversal_degrees / self._fps
                elif self._ships[ship_id].scanner_locked:
                    max_traversal = self._ships[ship_id].scanner_locked_max_traversal_degrees / self._fps
                else:
                    raise NotImplementedError
                if delta > max_traversal:
                    self._ships[ship_id].scanner_locked = False
                    self._ships[ship_id].scanner_locking = False
                    self._ships[ship_id].scanner_lock_target = None
                    self._ships[ship_id].scanner_lock_traversal_slack = None
                    self._ships[ship_id].scanner_lock_traversal_degrees_previous_frame = None
                else:
                    self._ships[ship_id].scanner_lock_traversal_degrees_previous_frame = self._ships[ship_id].scanner_data[
                        self._ships[ship_id].scanner_lock_target
                    ]['target_heading']
                    self._ships[ship_id].scanner_lock_traversal_slack = delta / max_traversal


    def calculate_weapons_and_damage(self, ship_id: str):
        death_data = self._ships[ship_id].advance_damage_properties(
            self._game_frame,
            self._map_x_unit_length,
            self._map_y_unit_length,
            MAX_SERVER_FPS,
        )

        ix_visual_type = 0
        ix_frames_since_death = 1

        if death_data and death_data[ix_frames_since_death] == 0:
            self._killfeed.append({
                "created_at_frame": self._game_frame,
                "victim_name": self._ships[ship_id].scanner_designator,
            })

        if death_data and death_data[ix_visual_type] == ShipDeathType.EXPLOSION_NEW:
            self._explosion_shockwaves.append({
                "id": str(uuid4()),
                "origin_point": self._ships[ship_id].coords,
                "radius_meters": 1,
            })

        if death_data:
            return

        if self._ships[ship_id].ebeam_firing:
            success = self._ships[ship_id].use_ebeam_charge(self._fps)
            if success:
                line, hits = self._get_ebeam_line_and_hit(self._ships[ship_id])
                self._ebeam_rays.append({
                    "start_point": line[0],
                    "end_point": line[1],
                    "color": self._ships[ship_id].ebeam_color,
                })

                if any(hits):
                    self._ships[ship_id].ebeam_last_hit_frame = self._game_frame

                for hit_ship_id in hits:
                    self._ships[hit_ship_id].die(self._game_frame)
                    self._killfeed.append({
                        "created_at_frame": self._game_frame,
                        "victim_name": self._ships[hit_ship_id].scanner_designator,
                    })

    def _get_ebeam_line_and_hit(self, ship: Ship) -> Tuple:
        # gets starting point of EBeam ray
        p1_x, p1_y = ship.map_p1
        p2_x, p2_y = ship.map_p2
        pm_x = round(p1_x + p2_x) / 2
        pm_y = round(p1_y + p2_y) / 2
        intercept_calculator, ray_point_b = utils2d.hitboxes_intercept_ray_factory(
            (pm_x, pm_y),
            ship.ebeam_heading,
            (self._map_x_unit_length, self._map_y_unit_length,),
        )
        line = (
            (pm_x, pm_y),
            ray_point_b,
        )
        hits = []
        for other_id, other_ship in self._ships.items():
            if other_id == ship.id or other_ship.died_on_frame:
                continue
            if intercept_calculator(other_ship.hitbox_lines):
                hits.append(other_id)

        return line, hits


    def check_for_winning_team(self):
        alive_teams = set(
            s.team_id for s in self._ships.values()
            if s.died_on_frame is None
            and s.team_id is not None
        )
        if len(alive_teams) == 1:
            self._winning_team = alive_teams.pop()

    def check_for_empty_game(self):
        if len(self._players) == 0:
            self._phase = GamePhase.COMPLETE

    def purge_killfeed(self, fps: int):
        oldest_frame = self._game_frame - fps * 8
        self._killfeed = [
            k for k in self._killfeed
            if k['created_at_frame'] >= oldest_frame
        ]

    def check_for_gravity_brake_catch(self, ship_id: str) -> True:
        if (
            self._ships[ship_id].gravity_brake_active
            or not self._ships[ship_id].gravity_brake_deployed
            or self._ships[ship_id].docked_at_station
        ):
            return

        for ix, st in enumerate(self._space_stations):
            dist = utils2d.calculate_point_distance(
                (st['position_map_units_x'], st['position_map_units_y']),
                self._ships[ship_id].coords,
            )
            if dist <= st['service_radius_map_units']:
                # Gravity Brake Catches
                self._ships[ship_id].engine_lit = False
                self._ships[ship_id].scanner_locked = False
                self._ships[ship_id].scanner_locking = False
                self._ships[ship_id].scanner_lock_traversal_slack = None
                self._ships[ship_id].scanner_lock_traversal_degrees_previous_frame = None
                self._ships[ship_id].scanner_lock_target = None
                self._ships[ship_id].gravity_brake_active = True
                self._ships[ship_id].docking_at_station = st['uuid']
                self._space_stations[ix]['grav_brake_last_caught'] = self._game_frame

    def check_for_ore_mine_parking(self, ship_id: str) -> None:
        ship = self._ships[ship_id]
        if not ship.is_stationary:
            self._ships[ship_id].parked_at_ore_mine = None
            return

        if ship.parked_at_ore_mine:
            return

        ship_coords = ship.coords
        for om in self._ore_mines:
            dist = utils2d.calculate_point_distance(
                (om['position_map_units_x'], om['position_map_units_y']),
                ship_coords,
            )
            if dist <= om['service_radius_map_units']:
                self._ships[ship_id].parked_at_ore_mine = om['uuid']
                return

        self._ships[ship_id].parked_at_ore_mine = None

    def advance_mining(self, ship_id: str):
        ship = self._ships[ship_id]
        if not ship.parked_at_ore_mine:
            self._ships[ship_id].mining_ore = False
            return
        if ship.mining_ore:
            adj = round(ship.mining_ore_kg_collected_per_second / self._fps, 2)
            room_for = min(adj, ship.cargo_ore_mass_capacity_kg - ship.cargo_ore_mass_kg)
            if room_for == 0:
                self._ships[ship_id].mining_ore = False
                return

            avail = self._ore_mines_remaining_ore[ship.parked_at_ore_mine]
            if avail == 0:
                self._ships[ship_id].mining_ore = False
                return
            adj = min(avail, adj)
            adj = min(room_for, adj)
            if adj > 0:
                self._ore_mines_remaining_ore[ship.parked_at_ore_mine] = max(
                    0,
                    self._ore_mines_remaining_ore[ship.parked_at_ore_mine] - adj
                )
                self._ships[ship_id].cargo_ore_mass_kg = min(
                    ship.cargo_ore_mass_capacity_kg,
                    ship.cargo_ore_mass_kg + adj
                )
            else:
                self._ships[ship_id].mining_ore = False

    def update_scouted_mine_ore_remaining(self, ship_id: str):
        ship = self._ships[ship_id]
        ship_coords = ship.coords
        for om in self._ore_mines:
            mine_uuid = om['uuid']
            dist_meters = utils2d.calculate_point_distance(
                (om['position_map_units_x'], om['position_map_units_y']),
                ship_coords,
            ) / self._map_units_per_meter
            scan_range = ship.scanner_range if ship.scanner_online else 0
            visual_range = ship.visual_range
            max_range = max(scan_range, visual_range)
            if dist_meters <= max_range:
                self._ships[ship_id].scouted_mine_ore_remaining[
                    mine_uuid
                ] = self._ore_mines_remaining_ore[mine_uuid]

    def _process_ship_command(self, command: FrameCommand):
        ship_command = command['ship_command']
        player_id = command['player_id']
        args = command.get('args', [])
        kwargs = command.get('kwargs', {})
        kwargs['game_frame'] = self._game_frame
        ship_id = self._player_id_to_ship_id_map[player_id]

        # Handle game level commands.
        if ship_command == ShipCommands.LEAVE_GAME:
            self.cmd_handle_player_leaving(player_id)

        else:
            # Handle ship level commands.
            self._ships[ship_id].process_command(
                ship_command,
                *args,
                **kwargs,
            )

    def cmd_handle_player_leaving(self, player_id: str):
        team_id = self._players[player_id]['team_id']
        ship_id = self._player_id_to_ship_id_map[player_id]
        players_on_team_count = len(
            [p for p in self._players.values() if p['team_id'] == team_id]
        )

        if players_on_team_count < 2:
            # If there are no more teammates to control the ship,
            # kill it and remove it from the dissolved team.
            self._ships[ship_id].died_on_frame = self._game_frame
            self._ships[ship_id].team_id = None

        del self._players[player_id]
