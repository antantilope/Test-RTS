
import argparse
import json
from typing import Dict
import socketserver

from api.models.game import Game


class TCPHandlerException(Exception):
    pass


class TCPHandler(socketserver.StreamRequestHandler):

    game = Game()

    # Phase 0
    CMD_ROOT_ADD_PLAYER = 'add_player'
    CMD_ROOT_CONFIGURE_MAP = 'configure_map'
    CMD_ROOT_ADVANCE_TO_PHASE_1_STARTING = 'advance_to_phase_1_starting'

    # Phase 1
    CMD_ROOT_DECR_PHASE_1_STARTING_COUNTDOWN = 'decr_phase_1_starting_countdown'

    # PHase 2
    CMD_ROOT_RUN_FRAME = 'run_frame'


    def read_stripped_line(self) -> bytes:
        return self.rfile.readline().strip()

    def build_write_payload(self) -> bytes:
        return json.dumps(self.game.get_state()).encode()

    def handle(self):
        payload = self.read_stripped_line()

        data: Dict = json.loads(payload.decode())
        command_root: str = next(iter(data.keys()))
        request = data[command_root]

        if command_root == self.CMD_ROOT_RUN_FRAME:
            self.game.run_frame(request)

        elif command_root == self.CMD_ROOT_ADD_PLAYER:
            self.game.register_player(request)

        elif command_root == self.CMD_ROOT_CONFIGURE_MAP:
            self.game.configure_map(request)

        elif command_root == self.CMD_ROOT_ADVANCE_TO_PHASE_1_STARTING:
            self.game.advance_to_phase_1_starting()

        elif command_root == self.CMD_ROOT_DECR_PHASE_1_STARTING_COUNTDOWN:
            self.game.decr_phase_1_starting_countdown()

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
