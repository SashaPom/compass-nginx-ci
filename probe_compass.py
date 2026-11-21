import math
import os
import subprocess
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Target:
    base_url: str
    release: str
    timeout: float


def read_target():
    base = os.environ.get("BASE_URL", "").strip().rstrip("/")
    release = os.environ.get("EXPECTED_RELEASE", "").strip()
    address = urlsplit(base)
    if address.scheme not in {"http", "https"} or not address.hostname:
        raise ValueError("BASE_URL must identify an HTTP server")
    if not release:
        raise ValueError("EXPECTED_RELEASE is required")
    timeout = float(os.environ.get("CHECK_TIMEOUT", "2.5"))
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("CHECK_TIMEOUT must be positive and finite")
    return Target(base, release, timeout)


def main():
    try:
        target = read_target()
    except ValueError as error:
        print(f"CONFIG ERROR | {error}")
        return 1

    url = target.base_url + "/"
    args = ["curl", "-q", "-fsS", "--noproxy", "*", "--", url]
    try:
        reply = subprocess.run(
            args, capture_output=True, text=True, timeout=target.timeout
        )
    except subprocess.TimeoutExpired:
        print(f"TIME LIMIT | {target.timeout:g}s | {url}")
        return 2
    except OSError as error:
        print(f"CURL ERROR | {error}")
        return 1

    if reply.returncode:
        print(f"CURL ERROR | exit {reply.returncode} | {reply.stderr.strip()}")
        return 1
    if target.release not in reply.stdout:
        print(f"RELEASE MISMATCH | expected {target.release}")
        return 1

    print(f"VERIFIED | {target.release} | {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
