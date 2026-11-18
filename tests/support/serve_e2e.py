"""Run the HTTP test server until the parent process closes its input."""

import sys
from threading import Thread

import uvicorn


def main() -> None:
    server = uvicorn.Server(
        uvicorn.Config("app.main:app", host="127.0.0.1", port=0, access_log=False)
    )

    def wait_for_shutdown() -> None:
        sys.stdin.buffer.read(1)
        server.should_exit = True

    Thread(target=wait_for_shutdown, daemon=True).start()
    server.run()


if __name__ == "__main__":
    main()
