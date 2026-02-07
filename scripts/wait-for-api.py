import os
import sys
import time
from urllib.request import urlopen


def main() -> int:
    base = os.getenv("API_BASE", "http://localhost:5556").rstrip("/")
    explicit_url = os.getenv("API_HEALTH_URL") or os.getenv("HEALTH_URL")
    if explicit_url:
        url = explicit_url.rstrip("/")
    else:
        health_path = os.getenv("API_HEALTH_PATH", "/health").strip()
        if not health_path.startswith("/"):
            health_path = f"/{health_path}"
        url = f"{base}{health_path}"
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
