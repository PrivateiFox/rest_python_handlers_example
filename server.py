import datetime
import http.server
from collections import deque
import threading
from typing import Final, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

# Server options
LISTENING_ADDRESS: Final[str] = 'localhost'
LISTENING_PORT: Final[int] = 8080
SHUTDOWN_POLL_INTERVAL: Final[float] = 0.5
MAX_SESSION_TIME: Final[datetime.timedelta] = datetime.timedelta(seconds=5)

# Runner options
CLOSE_STRING_CONDITION: Final[str] = ''  # Equivalent to <enter> - \n

# Shared thread context
client_id_sessions: Dict[int, Any] = {}
session_access_lock: threading.Lock = threading.Lock()


class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def _get_client_id(self) -> Optional[int]:
        parameters = parse_qs(urlparse(self.path).query)
        id_parameter: Optional[str] = parameters.get('clientId', None)
        if not id_parameter or len(id_parameter) != 1:
            return None

        client_id = int(id_parameter[0])  # Not checking if value can be converted to int(as instructed)
        return client_id

    @staticmethod
    def _get_new_session() -> Dict[str, Any]:
        return {'start_time': datetime.datetime.now(), 'count': 0}

    def _get_session_count(self, client_id: int) -> int:
        with session_access_lock:
            session = client_id_sessions.get(client_id, None)
            if (not session) or (datetime.datetime.now() - session['start_time'] > MAX_SESSION_TIME):
                session = self._get_new_session()
            session['count'] += 1
            client_id_sessions[client_id] = session
            return session['count']

    def do_GET(self) -> None:
        client_id = self._get_client_id()
        if client_id is None:
            self.send_error(400)

        count = self._get_session_count(client_id)

        if count > 5:
            self.send_error(503)
        else:
            self.send_response(200)
            self.end_headers()
        return


class HTTPServerThread(threading.Thread):
    def __init__(self, server: http.server.ThreadingHTTPServer):
        super().__init__()
        self.server = server

    def run(self) -> None:
        self.server.serve_forever(poll_interval=SHUTDOWN_POLL_INTERVAL)


def main() -> None:
    with http.server.ThreadingHTTPServer((LISTENING_ADDRESS, LISTENING_PORT),
                                         RequestHandlerClass=HTTPRequestHandler) as server:
        main_server_thread = HTTPServerThread(server)
        main_server_thread.start()
        while True:
            if input('Press enter to close the server.') == CLOSE_STRING_CONDITION:
                print('Stopping server.')
                server.shutdown()
                main_server_thread.join()
                break

    print('Main server stopped, exiting')


if __name__ == "__main__":
    main()
