
from collections import OrderedDict
from itertools import cycle
import json
import datetime as dt
from typing import Tuple, TypedDict, Optional, List, Dict, Set
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
    ScannedShipElement,
    MapMiningLocationDetails,
    MapSpaceStation,
    AutopilotError,
)
from .ship_designator import get_designations
from .special_weapons import (
    MagnetMine,
    EMP,
    HunterDrone,
)
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


class StartGameCountdownRequest(TypedDict):
    ship_asset_map: Dict[str, str]

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
    radius_meters: float

class Explosion(TypedDict):
    id: str
    ship_id: Optional[str]
    origin_point: Tuple[int]
    max_radius_meters: int
    radius_meters: float # TODO: Remve this field?
    flame_ms: float
    fade_ms: float
    elapsed_ms: int

class EMPBlast(TypedDict):
    id: str
    origin_point: Tuple[int]
    max_radius_meters: int
    flare_ms: float
    fade_ms: float
    elapsed_ms: int

class EBeamTargetingLine(TypedDict):
    mine_coord: Tuple[int]
    target_coord: Tuple[int]

class Game(BaseModel):

    BASE_STATE_KEYS = ('ok', 'phase', 'map_config', 'players',)

    def __init__(self):
        super().__init__()

        # This property (_is_testing) is a bit of an antipattern.
        # Ideally game logic should work exactly the same in unit tests
        # as it does in a live environment.
        # This field should only be referenced when you want CPU intensive
        # tasks to only run on every Nth frame, but for ease of testing
        # you want the task to run every frame. BE CAREFUL WHEN TIEING
        # LOGIC TO CODE PATHS THAT DONT RUN EVERY FRAME! - Jon
        self._is_testing = False

        self.logger = get_logger("Game-Logger")

        self._spawn_points: List[MapSpawnPoint] = []

        self._players: Dict[str, PlayerDetails] = {}
        self._ships: Dict[str, Ship] = OrderedDict()
        self._ebeam_rays: List[EBeamRayDetails] = []
        self._killfeed: List[KillFeedElement] = []
        self._explosion_shockwaves: List[ExplosionShockwave] = []
        self._ships_hit_by_shockwave: Dict[str, Set[str]] = {}
        self._explosions: List[Explosion] = []
        self._emp_blasts: List[EMPBlast] = []
        self._explosion_shockwave_max_radius_meters = None
        self._shockwave_max_delta_v_meters_per_second = constants.SHOCKWAVE_MAX_DELTA_V_METERS_PER_SECOND
        self._shockwave_max_delta_v_coef = constants.SHOCKWAVE_MAX_DELTA_V_COEF
        self._tube_weapon_recoil_meters_per_second = constants.TUBE_WEAPON_RECOIL_METERS_PER_SECOND
        self._space_stations: List[MapSpaceStation] = []
        self._ore_mines: List[MapMiningLocationDetails] = []
        self._ore_mines_remaining_ore: Dict[str, float] = {}

        self._magnet_mines: Dict[str, MagnetMine] = OrderedDict()
        self._emps: Dict[str, EMP] = OrderedDict()
        self._hunter_drones: Dict[str, HunterDrone] = OrderedDict()

        self._magnet_mine_targeting_lines: List[EBeamTargetingLine] = []

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

        self._colision_cycle_mine = "mine"
        self._colision_cycle_station = "station"
        self._colision_cycle_wall = "wall"
        self._collision_cycle = cycle((
            # self._colision_cycle_mine,
            # self._colision_cycle_station,
            self._colision_cycle_wall,
        ))

        # Special Weapons
        self._special_weapon_costs = {
            constants.MAGNET_MINE_SLUG: constants.MAGNET_MINE_ORE_COST,
            constants.EMP_SLUG: constants.EMP_ORE_COST,
            constants.HUNTER_DRONE_SLUG: constants.HUNTER_DRONE_COST,
        }
        self._magnet_mine_tracking_acceleration_ms = constants.MAGNET_MINE_TRACKING_ACCELERATION_MS
        self._magnet_mine_arming_time_seconds = constants.MAGNET_MINE_ARMING_TIME_SECONDS
        self._magnet_mine_max_seconds_to_detonate = constants.MAGNET_MINE_MAX_SECONDS_TO_DETONATE
        self._magnet_mine_max_proximity_to_explode_meters = constants.MAGNET_MINE_MAX_PROXIMITY_TO_EXPLODE_METERS
        self._magnet_mine_explode_damage_radius_meters = constants.MAGNET_MINE_EXPLODE_DAMAGE_RADIUS_METERS

        self._emp_max_seconds_to_detonate = constants.EMP_MAX_SECONDS_TO_DETONATE
        self._emp_max_proximity_to_explode_meters = constants.EMP_MAX_PROXIMITY_TO_EXPLODE_METERS
        self._emp_explode_damage_radius_meters = constants.EMP_EXPLODE_DAMAGE_RADIUS_METERS
        self._emp_electricity_drain = constants.EMP_ELECTRICITY_DRAIN

        self._hunter_drone_arming_time_seconds = constants.HUNTER_DRONE_ARMING_TIME_SECONDS
        self._hunter_drone_max_proximity_to_explode_meters = constants.HUNTER_DRONE_MAX_PROXIMITY_TO_EXPLODE_METERS
        self._hunter_drone_explode_damage_radius_meters = constants.HUNTER_DRONE_EXPLODE_DAMAGE_RADIUS_METERS

        self._heading_cache = CoordHeadingCache()
        self._distance_cache = CoordDistanceCache()

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
            'explosions': self._explosions,
            'emp_blasts': self._emp_blasts,
            "winning_team": self._winning_team,
            "killfeed": self._killfeed,
            "space_stations": self._space_stations,
            "ore_mines": self._ore_mines,
            "special_weapon_costs": self._special_weapon_costs,
            "magnet_mine_targeting_lines": self._magnet_mine_targeting_lines,
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

        self._explosion_shockwave_max_radius_meters = 4000

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


    def advance_to_phase_1_starting(self, request: StartGameCountdownRequest = None):
        self._validate_can_advance_to_phase_1_starting()
        self._phase = GamePhase.STARTING
        asset_map = request['ship_asset_map'] if request is not None else {}
        self._spawn_ships(asset_map)

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
    def _spawn_ships(self, asset_map: Dict[str, str]):
        """ TODO: Check for even spacing, add min_spacing value.
        """
        placed_points = []
        for ix, player_id in enumerate(self._players.keys()):
            team_id = self._players[player_id]['team_id']

            ship = Ship.spawn(
                team_id,
                self._special_weapon_costs,
                map_units_per_meter=self._map_units_per_meter,
                skin_slug=asset_map.get(player_id),
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

        if self._fps < MAX_SERVER_FPS:
            self.logger.warn(f"FPS<30: {self._fps}")

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

        for ship_id in self._ships:
            self._ships[ship_id].calculate_physics(self._fps, self._game_frame)

        self._heading_cache.clear()
        self._distance_cache.clear()

        for ship_id, ship in self._ships.items():
            ship.advance_upgrades(self._fps)
            ship.advance_gravity_brake_position(self._fps)
            ship.adjust_resources(self._fps, self._game_frame)
            ship.advance_heading_traversal(self._fps)
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

        self.advance_magnet_mines(self._fps)
        self.advance_emps(self._fps)
        self.advance_hunter_drones(self._fps)

        if any(self._explosions):
            self.advance_explosions()
        if any(self._emp_blasts):
            self.advance_emp_blasts()
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


    def _shock_wave_delta_v_calculator(self, distance: float) -> float:
        # calculate total magnitude a shockwave should have on an element
        # relative to the distance from the shock wave's center
        return max(
            0,
            self._shockwave_max_delta_v_coef * (distance**2) + self._shockwave_max_delta_v_meters_per_second
        )

    def advance_explosion_shockwaves(self):
        delta_radius = constants.SPEED_OF_SOUND_METERS_PER_SECOND / self._fps
        ix_to_remove = set()
        sw_ids_to_remove = set()
        check_for_sw_physics = self._is_testing or self._game_frame % 5 == 0
        for ix, esw in enumerate(self._explosion_shockwaves):
            # Adjust radius of shockwave
            new_radius = esw['radius_meters'] + delta_radius
            if new_radius > self._explosion_shockwave_max_radius_meters:
                ix_to_remove.add(ix)
                sw_ids_to_remove.add(esw['id'])
            else:
                self._explosion_shockwaves[ix]['radius_meters'] = new_radius

            # adjust ship velocities if they have been struck by the shock wave
            if check_for_sw_physics:
                for ship_id in self._ships:
                    if (
                        ship_id in self._ships_hit_by_shockwave[esw['id']]
                        or self._ships[ship_id].exploded
                        or self._ships[ship_id].docked_at_station
                        or self._ships[ship_id].docking_at_station
                    ):
                        continue
                    distance_meters = utils2d.calculate_point_distance(
                        self._ships[ship_id].coords,
                        esw['origin_point'],
                    ) / self._map_units_per_meter
                    if distance_meters <= esw['radius_meters']:
                        self._ships_hit_by_shockwave[esw['id']].add(ship_id)
                        acc_heading = utils2d.calculate_heading_to_point(
                            esw['origin_point'],
                            self._ships[ship_id].coords
                        )
                        delta_v_meters = self._shock_wave_delta_v_calculator(distance_meters)
                        if not delta_v_meters > 0:
                            continue
                        fx_meters, fy_meters = utils2d.calculate_x_y_components(
                            delta_v_meters,
                            acc_heading,
                        )
                        # No FPS calculation here, acceleration is instant
                        # and occurs over a single frame.
                        self._ships[ship_id].velocity_x_meters_per_second += fx_meters
                        self._ships[ship_id].velocity_y_meters_per_second += fy_meters

        if ix_to_remove:
            self._explosion_shockwaves = [
                esw
                for ix, esw in enumerate(self._explosion_shockwaves)
                if ix not in ix_to_remove
            ]
            self._ships_hit_by_shockwave = {
                k: v
                for k, v in self._ships_hit_by_shockwave.items()
                if k not in sw_ids_to_remove
            }

    def advance_explosions(self):
        ix_to_remove = []
        elapsed_ms = 1000 / self._fps
        for ix, ex in enumerate(self._explosions):
            if ex['elapsed_ms'] < (ex['flame_ms'] + ex['fade_ms']):
                self._explosions[ix]['elapsed_ms'] += elapsed_ms
            else:
                ix_to_remove.append(ix)
                if ex.get("ship_id"):
                    self._ships[ex['ship_id']]._removed_from_map = True

        if ix_to_remove:
            self._explosions = [
                ex
                for ix, ex in enumerate(self._explosions)
                if ix not in ix_to_remove
            ]


    def register_explosion_on_map(
        self,
        origin_point: Tuple[int],
        max_radius_meters: int,
        flame_ms: int,
        fade_ms: int,
        extras={}
    ):
        shockwave_id = str(uuid4())
        self._explosion_shockwaves.append({
            "id": shockwave_id,
            "origin_point": origin_point,
            "radius_meters": 1,
        })
        self._ships_hit_by_shockwave[shockwave_id] = set()
        self._explosions.append({
            "id": str(uuid4()),
            "origin_point": origin_point,
            "radius_meters": 1,
            "max_radius_meters": max_radius_meters,
            "flame_ms": flame_ms,
            "fade_ms": fade_ms,
            "elapsed_ms": 10,
            **extras,
        })

    def advance_emp_blasts(self):
        ix_to_remove = []
        elapsed_ms = 1000 / self._fps
        for ix, ex in enumerate(self._emp_blasts):
            if ex['elapsed_ms'] < (ex['flare_ms'] + ex['fade_ms']):
                self._emp_blasts[ix]['elapsed_ms'] += elapsed_ms
            else:
                ix_to_remove.append(ix)

        if ix_to_remove:
            self._emp_blasts = [
                ex
                for ix, ex in enumerate(self._emp_blasts)
                if ix not in ix_to_remove
            ]

    def reset_and_update_scanner_states(self, ship_id: str):

        self._ships[ship_id].scanner_ship_data.clear()
        self._ships[ship_id].scanner_magnet_mine_data.clear()
        self._ships[ship_id].scanner_emp_data.clear()
        self._ships[ship_id].scanner_hunter_drone_data.clear()

        ship_coords = self._ships[ship_id].coords
        scan_range = self._ships[ship_id].scanner_range if self._ships[ship_id].scanner_online else None
        visual_range = self._ships[ship_id].visual_range

        # Add ships to scanner data
        for other_id in (v for v in self._ships if v != ship_id):

            if self._ships[other_id]._removed_from_map:
                continue

            other_coords = self._ships[other_id].coords

            distance = self._distance_cache.get_val(ship_coords, other_coords)
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
                exact_heading = self._heading_cache.get_val(ship_coords, other_coords)
                other_scanner_online = self._ships[other_id].scanner_online
                other_scanner_mode = self._ships[other_id].scanner_mode
                scanner_ship_data: ScannedShipElement = {
                    'id': other_id,
                    'skin_slug': self._ships[other_id].skin_slug,
                    'designator': self._ships[other_id].scanner_designator,
                    'anti_radar_coating_level': self._ships[other_id].anti_radar_coating_level,
                    'scanner_thermal_signature': self._ships[other_id].scanner_thermal_signature,
                    'visual_scanner_mode': other_scanner_mode if other_scanner_online else None,
                    'visual_scanner_sensitivity': (
                        self._ships[other_id].scanner_radar_sensitivity
                        if other_scanner_online and other_scanner_mode == ShipScannerMode.RADAR
                        else None
                    ),
                    'visual_scanner_range_meters': self._ships[other_id].scanner_range if other_scanner_online else None,
                    'coord_x': other_coords[0],
                    'coord_y': other_coords[1],
                    'visual_heading': self._ships[other_id].heading,
                    'visual_map_nose_coord': self._ships[other_id].map_nose_coord,
                    'visual_map_bottom_left_coord': self._ships[other_id].map_bottom_left_coord,
                    'visual_map_bottom_right_coord': self._ships[other_id].map_bottom_right_coord,
                    'visual_map_bottom_center_coord': self._ships[other_id].map_bottom_center_coord,
                    'velocity_x_meters_per_second': self._ships[other_id].velocity_x_meters_per_second,
                    'velocity_y_meters_per_second': self._ships[other_id].velocity_y_meters_per_second,
                    'alive': self._ships[other_id].died_on_frame is None,
                    'aflame': self._ships[other_id].aflame_since_frame is not None,
                    'exploded': self._ships[other_id].exploded,
                    'in_visual_range': is_visual,
                    'visual_ebeam_charge_percent': self._ships[other_id].ebeam_charge / self._ships[other_id].ebeam_charge_capacity,
                    'visual_engine_lit': self._ships[other_id].engine_lit,
                    'visual_engine_boosted_last_frame': self._ships[other_id].engine_boosted_last_frame,
                    'visual_ebeam_firing': self._ships[other_id].ebeam_firing,
                    'visual_gravity_brake_position': self._ships[other_id].gravity_brake_position,
                    'visual_gravity_brake_deployed_position': self._ships[other_id].gravity_brake_deployed_position,
                    'visual_gravity_brake_active': self._ships[other_id].gravity_brake_active,
                    'visual_mining_ore_location': (
                        self._ships[other_id].parked_at_ore_mine
                        if self._ships[other_id].mining_ore
                        else None
                    ),
                    'visual_fueling_at_station': self._ships[other_id].fueling_at_station,
                    "visual_last_tube_fire_frame": self._ships[other_id].last_tube_fire_frame,
                    "distance": round(distance_meters),
                    "relative_heading": round(exact_heading),
                    "target_heading": exact_heading,
                }

                self._ships[ship_id].scanner_ship_data[other_id] = scanner_ship_data

        # Add magnet mines to scanner data
        for mm_id in self._magnet_mines:
            mine_coords = self._magnet_mines[mm_id].coords
            distance = utils2d.calculate_point_distance(ship_coords, mine_coords)
            distance_meters = round(distance / self._map_units_per_meter)
            is_visual = visual_range >= distance_meters
            is_scannable = (
                scan_range is not None
                and scan_range >= distance_meters
                and self._ships[ship_id].scanner_mode == ShipScannerMode.RADAR
            )
            if is_visual or is_scannable:
                exact_heading = utils2d.calculate_heading_to_point(ship_coords, mine_coords)
                self._ships[ship_id].scanner_magnet_mine_data[mm_id] = {
                    'id': mm_id,
                    'velocity_x_meters_per_second': self._magnet_mines[mm_id].velocity_x_meters_per_second,
                    'velocity_y_meters_per_second': self._magnet_mines[mm_id].velocity_y_meters_per_second,
                    'coord_x': mine_coords[0],
                    'coord_y': mine_coords[1],
                    'distance': distance_meters,
                    'exploded': self._magnet_mines[mm_id].exploded,
                    'relative_heading': round(exact_heading),
                    'percent_armed': self._magnet_mines[mm_id].percent_armed,
                }

        # Add EMPs to scanner data
        for emp_id in self._emps:
            emp_coords = self._emps[emp_id].coords
            distance = utils2d.calculate_point_distance(ship_coords, emp_coords)
            distance_meters = round(distance / self._map_units_per_meter)
            is_visual = visual_range >= distance_meters
            is_scannable = (
                scan_range is not None
                and scan_range >= distance_meters
                and self._ships[ship_id].scanner_mode == ShipScannerMode.RADAR
            )
            if is_visual or is_scannable:
                exact_heading = utils2d.calculate_heading_to_point(ship_coords, emp_coords)
                self._ships[ship_id].scanner_emp_data[emp_id] = {
                    'id': emp_id,
                    'coord_x': emp_coords[0],
                    'coord_y': emp_coords[1],
                    'distance': distance_meters,
                    'exploded': self._emps[emp_id].exploded,
                    'relative_heading': round(exact_heading),
                }

        # Add Hunter Drones to scanner data
        for hd_id in self._hunter_drones:
            drone_coords = self._hunter_drones[hd_id].coords
            distance = utils2d.calculate_point_distance(ship_coords, drone_coords)
            distance_meters = round(distance / self._map_units_per_meter)
            is_visual = visual_range >= distance_meters
            is_scannable = (
                scan_range is not None
                and scan_range >= distance_meters
            )
            if is_visual or is_scannable:
                exact_heading = utils2d.calculate_heading_to_point(ship_coords, drone_coords)
                self._ships[ship_id].scanner_hunter_drone_data[hd_id] = {
                    'id': hd_id,
                    'coord_x': drone_coords[0],
                    'coord_y': drone_coords[1],
                    'distance': distance_meters,
                    'exploded': self._hunter_drones[hd_id].exploded,
                    'visual_heading': self._hunter_drones[hd_id].heading,
                    'relative_heading': round(exact_heading),
                    'percent_armed': self._hunter_drones[hd_id].percent_armed,
                    'team_id': self._hunter_drones[hd_id].team_id,
                    'visual_map_bottom_center_coord': self._hunter_drones[hd_id].map_bottom_center_coord,
                }

        # Check if scanner target has gone out of range
        if self._ships[ship_id].scanner_lock_target and self._ships[ship_id].scanner_lock_target not in self._ships[ship_id].scanner_ship_data:
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
                self._ships[ship_id].scanner_lock_traversal_degrees_previous_frame = self._ships[ship_id].scanner_ship_data[
                    self._ships[ship_id].scanner_lock_target
                ]['target_heading']
            else:
                target_heading = self._ships[ship_id].scanner_ship_data[
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
                    self._ships[ship_id].scanner_lock_traversal_degrees_previous_frame = self._ships[ship_id].scanner_ship_data[
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
            is_firey = self._ships[ship_id].fuel_level > 6000
            self.register_explosion_on_map(
                self._ships[ship_id].coords,
                100 if is_firey else 65,
                3000 if is_firey else 1500,
                6000 if is_firey else 4500,
                extras={'ship_id': ship_id},
            )
        if death_data:
            return

        if self._game_frame % 2 == 0:
            collision_type = next(self._collision_cycle)
            death_data = self._advance_collisions(
                ship_id,
                collision_type,
            )
            if death_data:
                is_firey = self._ships[ship_id].fuel_level > 6000
                self._killfeed.append({
                    "created_at_frame": self._game_frame,
                    "victim_name": self._ships[ship_id].scanner_designator,
                })
                if death_data[ix_visual_type] == ShipDeathType.EXPLOSION_NEW:
                    self.register_explosion_on_map(
                        self._ships[ship_id].coords,
                        100 if is_firey else 65,
                        3000 if is_firey else 1500,
                        6000 if is_firey else 4500,
                        extras={'ship_id': ship_id},
                    )
                return


        # ELECTRO MAGNETIC ENERGY BEAM WEAPON
        if self._ships[ship_id].ebeam_firing:
            if self._ships[ship_id].use_ebeam_charge(self._fps):
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

        elif self._ships[ship_id].ebeam_autofire_enabled:
            if self._ships[ship_id].ebeam_charge < self._ships[ship_id].ebeam_charge_fire_minimum:
                pass

            elif self.search_for_firing_solution(ship_id):
                self._ships[ship_id].ebeam_firing = True
                if self._ships[ship_id].use_ebeam_charge(self._fps):
                    self._ships[ship_id].ebeam_autofire_enabled = False
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
                else:
                    print("not enough charge", self._fps, self._ships[ship_id].ebeam_charge)
                    self._ships[ship_id].ebeam_autofire_enabled = False


        apply_tubeweapon_recoil = False

        # SPECIAL WEAPONS (TUBE/TORPEDO WEAPONS)
        if self._ships[ship_id].magnet_mine_firing:
            # Spawn a new magnet mine.
            self._ships[ship_id].magnet_mine_firing = False
            self._ships[ship_id].last_tube_fire_frame = self._game_frame
            mine = MagnetMine(self._game_frame, ship_id)
            extra_x, extra_y = utils2d.calculate_x_y_components(
                self._ships[ship_id].magnet_mine_launch_velocity,
                self._ships[ship_id].heading,
            )
            mine.velocity_x_meters_per_second = extra_x + self._ships[ship_id].velocity_x_meters_per_second
            mine.velocity_y_meters_per_second = extra_y + self._ships[ship_id].velocity_y_meters_per_second
            mine.coord_x, mine.coord_y =  self._ships[ship_id].map_nose_coord
            self._magnet_mines[mine.id] = mine
            apply_tubeweapon_recoil = not self._ships[ship_id].recoilless_tube_launches

        elif self._ships[ship_id].emp_firing:
            # Spawn a new EMP
            self._ships[ship_id].emp_firing = False
            self._ships[ship_id].last_tube_fire_frame = self._game_frame
            emp = EMP(self._game_frame, ship_id)
            extra_x, extra_y = utils2d.calculate_x_y_components(
                self._ships[ship_id].emp_launch_velocity_ms,
                self._ships[ship_id].heading,
            )
            emp.velocity_x_meters_per_second = extra_x + self._ships[ship_id].velocity_x_meters_per_second
            emp.velocity_y_meters_per_second = extra_y + self._ships[ship_id].velocity_y_meters_per_second
            emp.coord_x, emp.coord_y =  self._ships[ship_id].map_nose_coord
            self._emps[emp.id] = emp
            apply_tubeweapon_recoil = not self._ships[ship_id].recoilless_tube_launches

        elif self._ships[ship_id].hunter_drone_firing:
            # Spawn a new Hunter Drone
            self._ships[ship_id].hunter_drone_firing = False
            self._ships[ship_id].last_tube_fire_frame = self._game_frame
            start_x, start_y = self._ships[ship_id].map_nose_coord
            extra_x, extra_y = utils2d.calculate_x_y_components(
                self._ships[ship_id].hunter_drone_launch_velocity,
                self._ships[ship_id].heading,
            )
            hunter_drone = HunterDrone(
                self._map_units_per_meter,
                self._game_frame,
                ship_id,
                self._ships[ship_id].team_id,
                self._ships[ship_id].heading,
                self._ships[ship_id].velocity_x_meters_per_second + extra_x,
                self._ships[ship_id].velocity_y_meters_per_second + extra_y,
                start_x,
                start_y,
                self._ships[ship_id]._hunter_drone_max_target_acquisition_distance_meters,
                self._ships[ship_id]._hunter_drone_tracking_acceleration_ms,
            )
            self._hunter_drones[hunter_drone.id] = hunter_drone
            apply_tubeweapon_recoil = not self._ships[ship_id].recoilless_tube_launches

        if apply_tubeweapon_recoil:
            recoil_x, recoil_y = utils2d.calculate_x_y_components(
                self._tube_weapon_recoil_meters_per_second,
                utils2d.invert_heading(self._ships[ship_id].heading),
            )
            self._ships[ship_id].velocity_x_meters_per_second += recoil_x
            self._ships[ship_id].velocity_y_meters_per_second += recoil_y


    def advance_magnet_mines(self, fps: int):
        keys_to_drop = []
        self._magnet_mine_targeting_lines.clear()
        arm_time_ms = self._magnet_mine_arming_time_seconds * 1000

        # Check if mine is within explosion range of any ship
        # and check if mine should accelerate towards a new target.
        check_proximity = self._is_testing or self._game_frame % 3 == 0

        for mm_id in self._magnet_mines:

            if self._magnet_mines[mm_id].exploded:
                keys_to_drop.append(mm_id)
                continue

            self._magnet_mines[mm_id].elapsed_milliseconds += (1000 / fps)

            # Arm the mine if enough time has passed
            if (
                not self._magnet_mines[mm_id].armed
                and self._magnet_mines[mm_id].elapsed_milliseconds > arm_time_ms
            ):
                self._magnet_mines[mm_id].armed = True
                self._magnet_mines[mm_id].percent_armed = 1

            elif not self._magnet_mines[mm_id].armed:
                self._magnet_mines[mm_id].percent_armed = (
                    self._magnet_mines[mm_id].elapsed_milliseconds / arm_time_ms
                )

            explode_mine = False
            if self._magnet_mines[mm_id].armed:
                trigger_radius = self._magnet_mine_max_proximity_to_explode_meters * self._map_units_per_meter
                damage_radius = self._magnet_mine_explode_damage_radius_meters * self._map_units_per_meter
                ship_id_distance_pairs = None
                if check_proximity or self._magnet_mines[mm_id].closest_ship_id is None:
                    # create ship, distance pairs
                    # sorted by shortest distance to longest distance.
                    ship_id_distance_pairs = sorted([
                        (
                            ship_id,
                            utils2d.calculate_point_distance(
                                self._magnet_mines[mm_id].coords,
                                self._ships[ship_id].coords,
                            )
                        )
                        for ship_id in self._ships
                        if not self._ships[ship_id].exploded
                    ], key=lambda pair: pair[1])

                    # Explode mine if close enough to target
                    # if nothing close enough, target mine towards closest ship.
                    if any(ship_id_distance_pairs):
                        self._magnet_mines[mm_id].closest_ship_id = ship_id_distance_pairs[0][0]
                        self._magnet_mines[mm_id].distance_to_closest_ship = ship_id_distance_pairs[0][1]
                        if ship_id_distance_pairs[0][1] <= trigger_radius:
                            explode_mine = True

                if not explode_mine:
                    if self._magnet_mines[mm_id].elapsed_milliseconds > (self._magnet_mine_max_seconds_to_detonate * 1000):
                        # explode mine if timer has expired
                        explode_mine = True
                        if ship_id_distance_pairs is None:
                            ship_id_distance_pairs = sorted([
                                (
                                    ship_id,
                                    utils2d.calculate_point_distance(
                                        self._magnet_mines[mm_id].coords,
                                        self._ships[ship_id].coords,
                                    )
                                )
                                for ship_id in self._ships
                                if not self._ships[ship_id].exploded
                            ], key=lambda pair: pair[1])


                if explode_mine:
                    self._magnet_mines[mm_id].exploded = True
                    self.register_explosion_on_map(
                        self._magnet_mines[mm_id].coords,
                        self._magnet_mine_explode_damage_radius_meters * 1.1,
                        1200,
                        2000,
                    )
                    for pair in ship_id_distance_pairs:
                        if pair[1] <= damage_radius:
                            self._ships[pair[0]].die(self._game_frame)
                        else:
                            break

                elif self._magnet_mines[mm_id].closest_ship_id:
                    # Accelerate towards closest target
                    heading_to_closest = utils2d.calculate_heading_to_point(
                        self._magnet_mines[mm_id].coords,
                        self._ships[self._magnet_mines[mm_id].closest_ship_id].coords,
                    )
                    x_acc, y_acc = utils2d.calculate_x_y_components(
                        self._magnet_mine_tracking_acceleration_ms / fps,
                        heading_to_closest,
                    )
                    self._magnet_mines[mm_id].velocity_x_meters_per_second += x_acc
                    self._magnet_mines[mm_id].velocity_y_meters_per_second += y_acc

                    # draw targeting line
                    self._magnet_mine_targeting_lines.append({
                        "mine_coord": self._magnet_mines[mm_id].coords,
                        "target_coord": self._ships[self._magnet_mines[mm_id].closest_ship_id].coords,
                    })

            # Adjust position
            if not explode_mine:
                self._magnet_mines[mm_id].coord_x += (
                    (self._magnet_mines[mm_id].velocity_x_meters_per_second
                    * self._map_units_per_meter)
                    / fps)
                self._magnet_mines[mm_id].coord_y += (
                    (self._magnet_mines[mm_id].velocity_y_meters_per_second
                    * self._map_units_per_meter)
                    / fps)

        # mines get deleted from dict on the frame after they explode.
        if any(keys_to_drop):
            for k in keys_to_drop:
                del self._magnet_mines[k]

    def advance_emps(self, fps: int):
        keys_to_drop = []

        # For a performance boost, only check proximity every 3rd frame
        check_proximity = self._is_testing or self._game_frame % 3 == 0

        for emp_id in self._emps:
            if self._emps[emp_id].exploded:
                keys_to_drop.append(emp_id)
                continue

            self._emps[emp_id].elapsed_milliseconds += (1000 / fps)

            # Blow up EMP if timer has expired
            explode = False
            if self._emps[emp_id].elapsed_milliseconds > (self._emp_max_seconds_to_detonate * 1000):
                explode = True

            if explode or check_proximity:
                ship_id_in_kill_range = []
                for ship_id in self._ships:
                    is_shooter = ship_id == self._emps[emp_id].ship_id
                    if self._ships[ship_id].exploded:
                        continue
                    distance_meters = utils2d.calculate_point_distance(
                        self._emps[emp_id].coords,
                        self._ships[ship_id].coords,
                    ) / self._map_units_per_meter
                    if not is_shooter and not explode and distance_meters <= self._emp_max_proximity_to_explode_meters:
                        # Blow up EMP if it's within proximity of an enemy ship
                        explode = True
                        ship_id_in_kill_range.append(ship_id)
                    elif distance_meters <= self._emp_explode_damage_radius_meters:
                        ship_id_in_kill_range.append(ship_id)
                if explode:
                    self._emps[emp_id].exploded = True
                    self._emp_blasts.append({
                        "id": str(uuid4()),
                        "origin_point": self._emps[emp_id].coords,
                        "max_radius_meters":  self._emp_explode_damage_radius_meters,
                        "flare_ms": 200,
                        "fade_ms": 3000,
                        "elapsed_ms": 10,
                    })
                    for ship_id in ship_id_in_kill_range:
                        self._ships[ship_id].emp(self._emp_electricity_drain)

            # Adjust position
            if not explode:
                self._emps[emp_id].coord_x += (self._emps[emp_id].velocity_x_meters_per_second * self._map_units_per_meter / fps)
                self._emps[emp_id].coord_y += (self._emps[emp_id].velocity_y_meters_per_second * self._map_units_per_meter / fps)

        # EMPs get deleted from dict on the frame after they  explode.
        if any(keys_to_drop):
            for k in keys_to_drop:
                del self._emps[k]


    def advance_hunter_drones(self, fps: int):
        keys_to_drop = []
        arm_time_ms = self._hunter_drone_arming_time_seconds * 1000

        # For a performance boost, only check proximity every 2nd frame
        check_proximity = self._is_testing or self._game_frame % 2 == 0

        for hd_id in self._hunter_drones:
            if self._hunter_drones[hd_id].exploded:
                keys_to_drop.append(hd_id)
                continue

            # Arm drone, or advance "percent armed" property
            # and position (no acceleration)
            if not self._hunter_drones[hd_id].armed:
                self._hunter_drones[hd_id].elapsed_milliseconds += (1000 / fps)
                if self._hunter_drones[hd_id].elapsed_milliseconds > arm_time_ms:
                    self._hunter_drones[hd_id].armed = True
                    self._hunter_drones[hd_id].percent_armed = 1
                else:
                    self._hunter_drones[hd_id].percent_armed = self._hunter_drones[hd_id].elapsed_milliseconds / arm_time_ms
                    self._hunter_drones[hd_id].coord_x += (
                        self._hunter_drones[hd_id].velocity_x_meters_per_second * self._map_units_per_meter / fps)
                    self._hunter_drones[hd_id].coord_y += (
                        self._hunter_drones[hd_id].velocity_y_meters_per_second * self._map_units_per_meter / fps)
                    continue

            # Drone armed, search for target
            if self._hunter_drones[hd_id].target_ship_id is None and check_proximity:
                min_distance_ship_id = None
                min_distance_map_units = None
                for ship_id in self._ships:
                    if self._hunter_drones[hd_id].team_id == self._ships[ship_id].team_id:
                        continue # ignore ship/team that launched drone.
                    distance = utils2d.calculate_point_distance(
                        self._ships[ship_id].coords,
                        self._hunter_drones[hd_id].coords,
                    )
                    if min_distance_ship_id is None or distance < min_distance_map_units:
                        min_distance_ship_id = ship_id
                        min_distance_map_units = distance
                if (
                    min_distance_map_units is not None
                    and (min_distance_map_units/self._map_units_per_meter) < self._hunter_drones[hd_id].max_acquisition_meters
                ):
                    # Target aquired
                    self._hunter_drones[hd_id].target_ship_id = min_distance_ship_id

            # Adjust heading
            target_ship_id = self._hunter_drones[hd_id].target_ship_id
            if target_ship_id is None:
                # No target: fly patrol.
                _, current_velocity_heading = utils2d.calculate_resultant_vector(
                    self._hunter_drones[hd_id].velocity_x_meters_per_second,
                    self._hunter_drones[hd_id].velocity_y_meters_per_second,
                )
                delta_degrees = (
                    90
                    if self._hunter_drones[hd_id].autopilot_patrol_pattern == HunterDrone.AUTOPILOT_PATROL_PATERN_CLOCKWISE else
                    -90
                )
                new_heading = utils2d.signed_angle_to_unsigned_angle(
                    current_velocity_heading
                    + delta_degrees
                )
                self._hunter_drones[hd_id].set_heading(new_heading)

            elif (
                target_ship_id is not None
                and self._ships[target_ship_id].exploded
            ):
                # original target exploded, clear targeting.
                # start flying patrol on next frame.
                self._hunter_drones[hd_id].target_ship_id = None
                target_ship_id = None

            elif (
                target_ship_id is not None
                and not self._ships[target_ship_id].exploded
            ):
                # Set intercept heading.
                intercept_angle = utils2d.calculate_heading_to_point(
                    self._hunter_drones[hd_id].coords,
                    self._ships[target_ship_id].coords,
                )
                _, velocity_angle = utils2d.calculate_resultant_vector(
                    self._hunter_drones[hd_id].velocity_x_meters_per_second,
                    self._hunter_drones[hd_id].velocity_y_meters_per_second,
                )
                intercept_angle_delta = utils2d.calculate_delta_degrees(
                    velocity_angle,
                    intercept_angle,
                )
                delta_magnitude = abs(intercept_angle_delta)
                if delta_magnitude < 5:
                    # Zero or tiny course correction. Accelerate on
                    # intercept angle.
                    self._hunter_drones[hd_id].set_heading(intercept_angle)
                elif delta_magnitude > 90:
                    # Fly retrograde heading to make large course correction.
                    self._hunter_drones[hd_id].set_heading(
                        utils2d.invert_heading(velocity_angle)
                    )
                else:
                    # Fly perpendicular to drones velocity line to
                    # in order to swing velocity line towards intercept line.
                    new_heading = utils2d.signed_angle_to_unsigned_angle(
                        velocity_angle
                        + (90 if intercept_angle_delta > 0 else -90)
                    )
                    self._hunter_drones[hd_id].set_heading(new_heading)

            # Apply acceleration and update position.
            acc_x, acc_y = utils2d.calculate_x_y_components(
                self._hunter_drones[hd_id].tracking_acceleration_ms/fps,
                self._hunter_drones[hd_id].heading,
            )
            self._hunter_drones[hd_id].velocity_x_meters_per_second += acc_x
            self._hunter_drones[hd_id].velocity_y_meters_per_second += acc_y
            self._hunter_drones[hd_id].coord_x += (
                self._hunter_drones[hd_id].velocity_x_meters_per_second*self._map_units_per_meter/fps)
            self._hunter_drones[hd_id].coord_y += (
                self._hunter_drones[hd_id].velocity_y_meters_per_second*self._map_units_per_meter/fps)

            # Check for proximity detonations and ship damamge.
            if check_proximity and target_ship_id is not None:
                distance_to_target = utils2d.calculate_point_distance(
                    self._hunter_drones[hd_id].coords,
                    self._ships[target_ship_id].coords,
                ) / self._map_units_per_meter
                if distance_to_target <= self._hunter_drone_max_proximity_to_explode_meters:
                    # Explode drone, kill target ship.
                    self._hunter_drones[hd_id].exploded = True
                    self.register_explosion_on_map(
                        self._hunter_drones[hd_id].coords,
                        self._hunter_drone_explode_damage_radius_meters * 1.1,
                        800,
                        1400,
                    )
                    self._ships[target_ship_id].die(self._game_frame)
                    # Kill any other ships within damage AOE.
                    for ship_id in self._ships:
                        if target_ship_id == ship_id:
                            continue # Already dead.
                        distance_to_ship = utils2d.calculate_point_distance(
                            self._hunter_drones[hd_id].coords,
                            self._ships[ship_id].coords,
                        ) / self._map_units_per_meter
                        if distance_to_ship <= self._hunter_drone_explode_damage_radius_meters:
                            self._ships[ship_id].die(self._game_frame)

        # Hunter Drone keys get deleted from dict on the frame after they explode.
        if any(keys_to_drop):
            for k in keys_to_drop:
                del self._hunter_drones[k]


    def _advance_collisions(self, ship_id: str, collision_type: str):
        if collision_type == self._colision_cycle_mine:
            for mine in self._ore_mines:
                dist = utils2d.calculate_point_distance(
                    (mine['position_map_units_x'], mine['position_map_units_y']),
                    self._ships[ship_id].coords,
                )
                if dist < (mine['collision_radius_meters'] * self._map_units_per_meter):
                    self._ships[ship_id].die(self._game_frame)
                    self._ships[ship_id].explode()
                    return ShipDeathType.EXPLOSION_NEW, 0

        elif collision_type == self._colision_cycle_station:
            for st in self._space_stations:
                dist = utils2d.calculate_point_distance(
                    (st['position_map_units_x'], st['position_map_units_y']),
                    self._ships[ship_id].coords,
                )
                if dist < (st['collision_radius_meters'] * self._map_units_per_meter):
                    self._ships[ship_id].die(self._game_frame)
                    self._ships[ship_id].explode()
                    return ShipDeathType.EXPLOSION_NEW, 0

        elif collision_type == self._colision_cycle_wall:
            if (
                self._ships[ship_id].coord_x < 0
                or self._ships[ship_id].coord_y < 0
                or self._ships[ship_id].coord_x > self._map_x_unit_length
                or self._ships[ship_id].coord_y > self._map_y_unit_length
            ):
                self._ships[ship_id].die(self._game_frame)
                self._ships[ship_id].explode()
                return ShipDeathType.EXPLOSION_NEW, 0
        else:
            raise NotImplementedError()


    def _get_ebeam_line_and_hit(self, ship: Ship) -> Tuple:
        pm_x, pm_y = ship.map_nose_coord
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

    def search_for_firing_solution(self, ship_id: str) -> bool:
        shooter_angle = self._ships[ship_id].heading
        ship_coords = self._ships[ship_id].coords
        for other_id, other_ship in self._ships.items():
            if other_id == ship_id or other_ship.died_on_frame:
                continue
            distance_meters = self._distance_cache.get_val(
                    ship_coords,
                    other_ship.coords,
            ) / self._map_units_per_meter
            if distance_meters > self._ships[ship_id].ebeam_autofire_max_range:
                continue

            bearings = tuple(
                self._heading_cache.get_val(
                    ship_coords,
                    hb_coord,
                )
                for hb_coord in other_ship.hitbox_coords
            )
            min_bearing = min(bearings)
            max_bearing = max(bearings)
            if (max_bearing - min_bearing) < 180:
                if min_bearing < shooter_angle < max_bearing:
                    return True
            else:
                # if one bearing = 1, and another bearing = 359, reorient bearings.
                bearings = tuple(
                    b + (360 if b < 180 else 0)
                    for b in bearings
                )
                shooter_angle += 360 if shooter_angle < 180 else 0
                if min(bearings) < shooter_angle < max(bearings):
                    return True

        return False


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
                self._ships[ship_id].scouted_station_gravity_brake_catches_last_frame[
                    st['uuid']
                ] = self._game_frame

                # Update Fog of War for other ships
                for other_id in (i for i in self._ships if i != ship_id):
                    dist = utils2d.calculate_point_distance(
                        (st['position_map_units_x'], st['position_map_units_y']),
                        self._ships[other_id].coords,
                    )
                    if dist <= (self._ships[other_id].current_FOW_vision * self._map_units_per_meter):
                        self._ships[other_id].scouted_station_gravity_brake_catches_last_frame[
                            st['uuid']
                        ] = self._game_frame

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
