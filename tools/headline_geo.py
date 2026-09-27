"""Use the shared offline headline resolver; unavailable geography stays unknown."""
from functools import lru_cache
import json
import pathlib
import subprocess


@lru_cache(maxsize=16)
def _locate_titles(titles: tuple[str, ...]) -> tuple[dict, ...]:
    if not titles:
        return ()
    fallback = tuple({"scope": "unknown", "status": "unknown", "estimate": None,
                      "candidates": [], "reason": "resolver_unavailable"} for _ in titles)
    try:
        process = subprocess.run(
            ["node", str(pathlib.Path(__file__).with_suffix('.js')), "--json"],
            input=json.dumps(titles, ensure_ascii=False), capture_output=True,
            encoding="utf-8", timeout=15, check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        results = json.loads(process.stdout)
        if not isinstance(results, list) or len(results) != len(titles):
            return fallback
        if any(not isinstance(row, dict) or row.get('scope') not in
               ('belgrade', 'serbia', 'outside', 'unknown') for row in results):
            return fallback
        return tuple(results)
    except (OSError, ValueError, subprocess.SubprocessError):
        return fallback


def locate_headlines(rows: list) -> list[dict]:
    # Only the headline establishes the event location. The publisher's identity,
    # URL and headquarters must never become a geographic cue.
    titles = tuple(str(row.get('title') or row.get('headline') or row.get('input_headline') or '')
                   if isinstance(row, dict) else str(row or '') for row in rows)
    return list(_locate_titles(titles))


def local_estimate(location: dict) -> bool:
    return (location.get('scope') == 'belgrade' and location.get('status') == 'estimated'
            and isinstance(location.get('estimate'), dict))
