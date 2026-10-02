# Lock probe for the live publish write lock. A previous cycle that still holds
# the exclusive lock makes a new attempt wait 120 s and burn a failed receipt
# (observed 2026-09-30 seq 2 -> seq 3), so admission asks this probe first:
# exit 0 = free, exit 75 = busy, other = probe error. The lock itself stays
# owned by contracts.exclusive; the probe never writes and never waits.
import json
import pathlib
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from contracts import exclusive  # noqa: E402

DEFAULT_LOCK = TOOLS.parent / "data" / "live" / ".write.lock"


def probe(path):
    try:
        with exclusive(path, timeout=0):
            return 0, "free"
    except TimeoutError:
        return 75, "busy"


if __name__ == "__main__":
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LOCK
    code, state = probe(path)
    print(json.dumps({"path": str(path), "state": state}))
    sys.exit(code)
