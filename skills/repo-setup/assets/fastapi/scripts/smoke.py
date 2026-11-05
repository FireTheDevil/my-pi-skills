"""Start uvicorn on an OS-assigned localhost socket; verify HTTP behavior."""

import json
import socket
import sys
import threading
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import uvicorn


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config("app.main:app", log_level="error"))
        worker = threading.Thread(
            target=server.run, kwargs={"sockets": [listener]}, daemon=True
        )
        worker.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started:
                if not worker.is_alive() or time.monotonic() > deadline:
                    raise RuntimeError("Service failed to start")
                time.sleep(0.05)
            origin = f"http://127.0.0.1:{port}"
            with urlopen(origin + "/health", timeout=3) as response:
                if json.load(response) != {"status": "ok"}:
                    raise RuntimeError("Health response mismatch")
            request = Request(
                origin + "/greet",
                data=json.dumps({"name": "Ada"}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urlopen(request, timeout=3) as response:
                if json.load(response) != {"message": "Hello, Ada!"}:
                    raise RuntimeError("Greeting response mismatch")
            request.data = b'{"name":" "}'
            try:
                urlopen(request, timeout=3).close()
            except HTTPError as error:
                if error.code != 422:
                    raise
                error.close()
            else:
                raise RuntimeError("Blank name was accepted")
            print("PASS: HTTP health, greeting and invalid-input rejection")
        finally:
            server.should_exit = True
            worker.join(timeout=5)
            if worker.is_alive():
                raise RuntimeError("Service did not shut down")


if __name__ == "__main__":
    main()
