
from unittest import TestCase

from api.models.game import Game, GamePhase, GameError


class TestGame(TestCase):

    def test_game_has_unique_id(self):
        game = Game()
        assert isinstance(game.id, str)
        assert len(game.id) > 10
        assert game.id != Game().id

    def test_game_starts_out_in_lobby_mode(self):
        game = Game()
        assert game._phase == GamePhase.LOBBY

    def test_game_map_is_not_configued_when_created(self):
        game = Game()
        assert not game.map_is_configured

    def test_game_can_register_player_when_in_lobby_phase(self):
        game = Game()
        game._phase = GamePhase.LOBBY
        game.register_player({
            'player_name': 'foobar',
            'player_id': '666777888',
        })
        assert len(game._players) == 1
        assert game._players['666777888'] == {
            'player_name': 'foobar',
            'player_id': '666777888',
        }

    def test_game_cannot_register_duplicate_player_id(self):
        game = Game()
        game._phase = GamePhase.LOBBY
        game._players['666777888'] = {
            'player_name': 'foobar',
            'player_id': '666777888',
        }
        assert len(game._players) == 1
        self.assertRaises(
            GameError,
            lambda: game.register_player({
                'player_name': 'foobar',
                'player_id': '666777888', # This id is already registered
            })
        )
        assert len(game._players) == 1

    def test_game_cannot_register_player_if_at_player_limit(self):
        game = Game()
        game._phase = GamePhase.LOBBY
        game._max_players = 1
        game._players['666777888'] = {
            'player_name': 'foobar',
            'player_id': '666777888',
        }
        assert len(game._players) == 1
        self.assertRaises(
            GameError,
            lambda: game.register_player({
                'player_name': 'foobar',
                'player_id': '999888777',
            })
        )
        assert len(game._players) == 1

        # Increase the limit and we can add.
        game._max_players = 2
        game.register_player({
            'player_name': 'foobar',
            'player_id': '999888777',
        })
        assert len(game._players) == 2

    def test_game_cannot_register_player_if_not_in_lobby_phase(self):
        game = Game()
        for phase in GamePhase.NON_LOBBY_PHASES:
            game._phase = phase
            self.assertRaises(
                GameError,
                lambda: game.register_player({
                    'player_name': 'foobar',
                    'player_id': '666777888',
                })
            )
            assert len(game._players) == 0

    def test_can_configure_map_during_lobby_phase(self):
        game = Game()
        game._phase = GamePhase.LOBBY

        assert not game.map_is_configured
        game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 10_000,
            'y_unit_length': 12_000,
        })
        assert game.map_is_configured
        assert game._map_units_per_meter == 10
        assert game._map_x_unit_length == 10_000
        assert game._map_y_unit_length == 12_000

        game.configure_map({
            'units_per_meter': 11,
            'x_unit_length': 11_000,
            'y_unit_length': 13_000,
        })
        assert game.map_is_configured
        assert game._map_units_per_meter == 11
        assert game._map_x_unit_length == 11_000
        assert game._map_y_unit_length == 13_000

    def test_game_cannot_configure_map_if_not_in_lobby_phase(self):
        game = Game()
        assert not game.map_is_configured
        for phase in GamePhase.NON_LOBBY_PHASES:
            game._phase = phase
            self.assertRaises(
                GameError,
                lambda: game.configure_map({
                    'units_per_meter': 10,
                    'x_unit_length': 10_000,
                    'y_unit_length': 12_000,
                })
            )
            assert not game.map_is_configured

    def test_game_can_advance_to_from_lobby_phase_to_start_phase(self):
        game = Game()
        game._phase = GamePhase.LOBBY

        game._players['666777888'] = {
            'player_name': 'foobar1',
            'player_id': '666777888',
            'team_id': '3546235',
        }
        game._players['1112223333'] = {
            'player_name': 'foobar2',
            'player_id': '1112223333',
            'team_id': '06786785',
        }
        game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 10_000,
            'y_unit_length': 12_000,
        })

        game.advance_to_phase_1_starting()
        assert game._phase == GamePhase.STARTING
        assert len(game._ships) == 2

    def test_game_cant_advance_to_from_to_start_phase_if_not_lobby_phase(self):
        game = Game()

        game._players['666777888'] = {
            'player_name': 'foobar1',
            'player_id': '666777888',
            'team_id': '06876856',
        }
        game._players['1112223333'] = {
            'player_name': 'foobar2',
            'player_id': '1112223333',
            'team_id': '54783456',
        }
        game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 10_000,
            'y_unit_length': 12_000,
        })
        for phase in GamePhase.NON_LOBBY_PHASES:
            game._phase = phase
            self.assertRaises(
                GameError,
                lambda: game.advance_to_phase_1_starting()
            )
            assert len(game._ships) == 0

    def test_game_cant_advance_to_from_to_start_phase_if_not_enough_players(self):
        game = Game()

        # Need 2 players
        game._players['666777888'] = {
            'player_name': 'foobar1',
            'player_id': '666777888',
            'team_id': '656566565',
        }
        game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 10_000,
            'y_unit_length': 12_000,
        })
        game._phase = GamePhase.LOBBY
        self.assertRaises(
            GameError,
            lambda: game.advance_to_phase_1_starting()
        )
        assert len(game._ships) == 0

        # Can start once we have 2 players
        game._players['1112223333'] = {
            'player_name': 'foobar2',
            'player_id': '1112223333',
            'team_id': '775686565',
        }
        game.advance_to_phase_1_starting()
        assert game._phase == GamePhase.STARTING
        assert len(game._ships) == 2

    def test_game_cant_advance_to_from_to_start_phase_if_map_not_configured(self):
        game = Game()
        game._phase = GamePhase.LOBBY

        game._players['666777888'] = {
            'player_name': 'foobar1',
            'player_id': '666777888',
            'team_id': '3546235',
        }
        game._players['1112223333'] = {
            'player_name': 'foobar2',
            'player_id': '1112223333',
            'team_id': '6457476',
        }
        # Missing map config.

        self.assertRaises(
            GameError,
            lambda: game.advance_to_phase_1_starting()
        )
        assert len(game._ships) == 0

        game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 10_000,
            'y_unit_length': 12_000,
        })
        game.advance_to_phase_1_starting()
        assert game._phase == GamePhase.STARTING
        assert len(game._ships) == 2
        for ship in game._ships.values():
            assert ship.map_units_per_meter == 10

    def test_spawn_ships_sets_player_id_to_ship_id_map(self):
        game = Game()
        game._phase = GamePhase.LOBBY

        game._players['666777888'] = {
            'player_name': 'foobar1',
            'player_id': '666777888',
            'team_id':'123456',
        }
        game._players['1112223333'] = {
            'player_name': 'foobar2',
            'player_id': '1112223333',
            'team_id':'665544',
        }
        game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 10_000,
            'y_unit_length': 12_000,
        })
        game.advance_to_phase_1_starting()

        assert len(game._player_id_to_ship_id_map) == 2
        assert '666777888' in game._player_id_to_ship_id_map
        assert '1112223333' in game._player_id_to_ship_id_map
        assert len(game._team_id_to_ship_id_map) == 2
        assert '123456' in game._team_id_to_ship_id_map
        assert '665544' in game._team_id_to_ship_id_map

    def test_spawn_ships_places_ships_in_bounds(self):
        for _i in range(100):

            game = Game()
            game._phase = GamePhase.LOBBY

            game._players['666777888'] = {
                'player_name': 'foobar1',
                'player_id': '666777888',
                'team_id':'4563453',
            }
            game._players['1112223333'] = {
                'player_name': 'foobar2',
                'player_id': '1112223333',
                'team_id':'756854',
            }
            game.configure_map({
                'units_per_meter': 10,
                'x_unit_length': 10_000,
                'y_unit_length': 12_000,
            })
            game.advance_to_phase_1_starting()

            for ship in game._ships.values():
                assert game._map_x_unit_length > ship.coord_x > 0
                assert game._map_y_unit_length > ship.coord_y > 0

    def test_can_decr_phase_1_starting_countdown(self):
        game = Game()
        game._phase = GamePhase.LOBBY

        game._players['666777888'] = {
            'player_name': 'foobar1',
            'player_id': '666777888',
            'team_id':'7698554',
        }
        game._players['1112223333'] = {
            'player_name': 'foobar2',
            'player_id': '1112223333',
            'team_id':'78654564',
        }
        game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 10_000,
            'y_unit_length': 12_000,
        })
        game.advance_to_phase_1_starting()

        assert game._game_start_countdown == 6
        game.decr_phase_1_starting_countdown()
        assert game._game_start_countdown == 5

    def test_can_decr_phase_1_starting_countdown_to_zero_which_advances_to_phase_2_live(self):
        game = Game()
        game._phase = GamePhase.LOBBY

        game._players['666777888'] = {
            'player_name': 'foobar1',
            'player_id': '666777888',
            'team_id':'778456982',
        }
        game._players['1112223333'] = {
            'player_name': 'foobar2',
            'player_id': '1112223333',
            'team_id':'0643255',
        }
        game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 10_000,
            'y_unit_length': 12_000,
        })
        game.advance_to_phase_1_starting()
        game._game_start_countdown = 1
        assert game._game_start_time is None

        game.decr_phase_1_starting_countdown()
        assert game._game_start_countdown == 0
        assert game._phase == GamePhase.LIVE
        assert game._game_frame == 1
        assert game._game_start_time is not None

    def test_game_detects_winning_team(self):
        game = Game()
        game._phase = GamePhase.LOBBY

        game._players['666777888'] = {
            'player_name': 'foobar1',
            'player_id': '666777888',
            'team_id': '3546235',
        }
        game._players['1112223333'] = {
            'player_name': 'foobar2',
            'player_id': '1112223333',
            'team_id': '06786785',
        }
        game.configure_map({
            'units_per_meter': 10,
            'x_unit_length': 10_000,
            'y_unit_length': 12_000,
        })
        game.advance_to_phase_1_starting()
        assert game._phase == GamePhase.STARTING
        assert len(game._ships) == 2
        game._phase = GamePhase.LIVE

        game.check_for_winning_team()
        assert game._winning_team is None

        player_1_ship = game._player_id_to_ship_id_map['666777888']
        game._ships[player_1_ship].died_on_frame = 1 # kill player1's ship

        game.check_for_winning_team()
        assert game._winning_team == '06786785' # Player2's team is the winner
