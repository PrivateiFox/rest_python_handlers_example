import random
import threading
import time
from typing import Final

import requests

# Client options
MIN_RANDOM_TIME: Final[int] = 0
MAX_RANDOM_TIME: Final[int] = 5
BASE_URL: Final[str] = 'http://localhost:8080'
CLIENT_ID_PARAMETER: Final[str] = 'clientId'

# Runner options
MIN_CLIENT_IDENTIFIER: Final[int] = 1
MAX_CLIENT_IDENTIFIER: Final[int] = 10
CLOSE_STRING_CONDITION: Final[str] = ''  # Equivalent to <enter> - \n


class Client(threading.Thread):
    def __init__(self, identifier: int, close_event: threading.Event):
        super().__init__()
        self.request_parameters = {CLIENT_ID_PARAMETER: identifier}
        self.close_event = close_event

    def run(self) -> None:
        while True:
            request = requests.get(BASE_URL, params=self.request_parameters)
            if self.close_event.is_set():
                break

            if request.status_code != 200:
                print(f'Received status code {request.status_code} '
                      f'in thread with client id: {self.request_parameters[CLIENT_ID_PARAMETER]}')

            time.sleep(random.randrange(MIN_RANDOM_TIME, MAX_RANDOM_TIME))


def main() -> None:
    close_event = threading.Event()
    client_count = int(input("Please enter the number of clients to use: "))

    clients = []
    for _ in range(client_count):
        # Different threads are allowed to share the same identifier
        client = Client(random.randrange(MIN_CLIENT_IDENTIFIER, MAX_CLIENT_IDENTIFIER), close_event)
        clients.append(client)
        client.start()

    while True:
        if input('Press enter to close the client.') == CLOSE_STRING_CONDITION:
            close_event.set()
            break

    print('Draining threads(clients)')
    for client in clients:
        client.join()
    print('All clients stopped, exiting')


if __name__ == "__main__":
    main()
