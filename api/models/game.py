
import random
from typing import TypedDict, Optional, List, Dict
import uuid

from .base import BaseModel
from .ship import Ship


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

        self._fps = 20


    def get_state(self) -> GameState:
        base_state = {
            'phase': self._phase,
            'game_frame': self._game_frame,
            'players': self._players,
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
            'ships': [],
        }


    # Phase 0 # #
    def register_player(self, request: PlayerDetails):
        self._validate_can_add_player(request['player_id'])
        self._players[request['player_id']] = request


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
        for ship_id, ship in self._ships.items():
            self._ships[ship_id].game_frame = self._game_frame

            # Phase 0
            self._calculate_ship_damage(ship)
            # Phase 1
            self._calculate_ship_resources(ship)
            # Phase 2
            self._calculate_physics(ship)
            # Phase 3
            self._calculate_ship_side_effects(ship)

        # Phase 4
        for command in request['commands']:
            self._process_ship_command(command)

        self.incr_game_frame()


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


    def _calculate_ship_damage(self, ship: Ship):
        ship.calculate_damage()

    def _calculate_ship_resources(self, ship: Ship):
        ship.adjust_resources()

    def _calculate_physics(self, ship: Ship):
        ship.calculate_physics(self._fps)

    def _calculate_ship_side_effects(self, ship: Ship):
        ship.calculate_side_effects()
