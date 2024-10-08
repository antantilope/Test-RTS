
import argparse
from functools import wraps
import json
from typing import Dict
import socketserver
import traceback

from api.models.game import Game
from api.logger import get_logger


class TCPHandlerException(Exception):
    pass



def log_handle(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            self.tcplogger.error(str(e))
            self.tcplogger.error(tb)
            raise

    return wrapper


class TCPHandler(socketserver.StreamRequestHandler):

    game = Game()

    tcplogger = get_logger("tcp")


    # Debug
    CMD_ROOT_PING = 'ping'

    # Phase 0
    CMD_ROOT_ADD_PLAYER = 'add_player'
    CMD_ROOT_REMOVE_PLAYER = 'remove_player'
    CMD_ROOT_SET_MAP = "set_map"
    CMD_ROOT_ADVANCE_TO_PHASE_1_STARTING = 'advance_to_phase_1_starting'

    # Phase 1
    CMD_ROOT_DECR_PHASE_1_STARTING_COUNTDOWN = 'decr_phase_1_starting_countdown'

    # PHase 2
    CMD_ROOT_RUN_FRAME = 'run_frame'


    def read_stripped_line(self) -> bytes:
        return self.rfile.readline().strip()

    def build_write_payload(self) -> bytes:
        return json.dumps(self.game.get_state()).encode()

    def build_ping_response(self) -> bytes:
        data = {
            k: v
            for k, v in self.game.get_state().items()
            if k in self.game.BASE_STATE_KEYS
        }
        return json.dumps(data).encode()

    @log_handle
    def handle(self):
        payload = self.read_stripped_line()

        data: Dict = json.loads(payload.decode())
        command_root: str = next(iter(data.keys()))

        request = data[command_root]

        if command_root == self.CMD_ROOT_RUN_FRAME:
            self.game.run_frame(request)

        elif command_root == self.CMD_ROOT_ADD_PLAYER:
            self.game.register_player(request)

        elif command_root == self.CMD_ROOT_REMOVE_PLAYER:
            player_id = request
            self.game.remove_player(player_id)

        elif command_root == self.CMD_ROOT_SET_MAP:
            self.game.set_map(request)

        elif command_root == self.CMD_ROOT_ADVANCE_TO_PHASE_1_STARTING:
            self.game.advance_to_phase_1_starting(request)

        elif command_root == self.CMD_ROOT_DECR_PHASE_1_STARTING_COUNTDOWN:
            self.game.decr_phase_1_starting_countdown()

        elif command_root == self.CMD_ROOT_PING:
            self.wfile.write(self.build_ping_response())
            return

        else:
            raise TCPHandlerException("NotImplementedError")


        self.wfile.write(self.build_write_payload())



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start Socket Server')
    parser.add_argument(
        'port',
        type=int,
        help='Port for process to run on.'
    )
    args = parser.parse_args()

    HOST, PORT = "localhost", args.port
    with socketserver.TCPServer((HOST, PORT), TCPHandler) as server:
        print("listening...")
        server.serve_forever()
