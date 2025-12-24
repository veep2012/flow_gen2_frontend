import os
import sys
import time
from urllib.request import urlopen


def main() -> int:
    base = os.getenv("API_BASE", "http://localhost:5556").rstrip("/")
    prefix = os.getenv("API_PREFIX", "").rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    url = f"{base}{prefix}/health"
    timeout = float(os.getenv("API_WAIT_TIMEOUT", "30"))
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2) as resp:
                if 200 <= resp.status < 300:
                    print("API ready")
                    return 0
        except Exception:
            time.sleep(0.5)

    print("API not ready for smoke tests.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
