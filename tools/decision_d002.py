"""Prepare immutable, deterministic D-002 replay candidates from one frozen snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pathlib
from datetime import datetime, timedelta, timezone


CLOCK_RANK = {"corrected_measurement": 3, "measurement": 2, "reception_only": 1}


def canonical_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(value) -> str:
    data = value if isinstance(value, bytes) else canonical_bytes(value)
    return hashlib.sha256(data).hexdigest()


def parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except ValueError:
        return None


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_bounded(path: pathlib.Path, limit: int) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError(f"input too large: {path.name}")
    value = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path.name}")
    return raw, value


def validate_policy(policy: dict) -> None:
    if policy.get("schema") != "beops-d002-policy/v1" or policy.get("decision_id") != "D-002":
        raise ValueError("invalid D-002 policy")
    signal = policy.get("signal") or {}
    if signal.get("minimum_points") != 3 or signal.get("minimum_persistent_intervals") != 2:
        raise ValueError("D-002 v1 requires three points and two persistent intervals")
    if policy.get("alternatives") != ["proveri_sada", "nastavi_pracenje", "nedovoljno_dokaza"]:
        raise ValueError("invalid alternatives")
    if not 1 <= policy.get("retain_ranked_candidates_per_episode", 12) <= 50:
        raise ValueError("invalid retained candidate count")
    for sid, source in (policy.get("sources") or {}).items():
        if not sid.startswith("S") or not source.get("domain") or not source.get("bindings"):
            raise ValueError("invalid source policy")
        if not 300 <= source.get("expected_cadence_seconds", 0) <= 86400:
            raise ValueError("invalid source cadence")


def point_clock(point: dict):
    corrected = parse_time(point.get("tc"))
    measured = parse_time(point.get("t")) if point.get("tu") is not True else None
    received = parse_time(point.get("rx"))
    if corrected:
        return corrected, "corrected_measurement"
    if measured:
        return measured, "measurement"
    if received:
        return received, "reception_only"
    return None, None


def frozen_point(sid: str, source: dict, stream: dict, point: dict) -> dict:
    event_time, clock = point_clock(point)
    row = {
        "sid": sid,
        "source": source.get("name"),
        "stream": stream.get("datastream"),
        "station": stream.get("station"),
        "property": stream.get("parameter"),
        "unit": stream.get("unit"),
        "value": point.get("v"),
        "phenomenon_or_effective_time": iso(event_time),
        "source_reported_time": point.get("t"),
        "published_or_result_time": point.get("rt"),
        "received_time": point.get("rx"),
        "clock": clock,
        "quality": point.get("q"),
    }
    row["evidence_id"] = digest(row)
    return row


def stream_points(sid: str, source: dict, stream: dict, cutoff: datetime) -> list[dict]:
    unique = {}
    for point in stream.get("points") or []:
        value = point.get("v")
        event_time, clock = point_clock(point)
        received = parse_time(point.get("rx"))
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            continue
        if not event_time or not received or event_time > cutoff or received > cutoff:
            continue
        key = (clock, iso(event_time))
        old = unique.get(key)
        if old is None or parse_time(old.get("rx")) < received:
            unique[key] = point
    rows = [frozen_point(sid, source, stream, point) for point in unique.values()]
    return sorted(rows, key=lambda row: (row["phenomenon_or_effective_time"], row["received_time"], row["evidence_id"]))


def permission_projection(root: pathlib.Path, policy: dict, now: datetime) -> dict:
    import permission_policy
    ledger = permission_policy.latest(root / "research/08-provenance/LEDGER.jsonl")
    collectors = json.loads((root / "research/COLLECTORS.json").read_text(encoding="utf-8"))
    by_sid = {row["sid"]: row for row in collectors["sources"]}
    result = {}
    for sid in policy["sources"]:
        source = by_sid.get(sid)
        if not source or not source.get("enabled", True):
            result[sid] = {"allowed": False, "checked_at": iso(now), "evidence": "collector absent or disabled"}
            continue
        url = source["url"].replace("{from_iso}", iso(now - timedelta(hours=2)))
        allowed, evidence = permission_policy.authorize(sid, ledger, root, url, now)
        result[sid] = {"allowed": allowed, "checked_at": iso(now), "evidence": evidence}
    return result


def build_episode(snapshot: dict, policy: dict, cutoff: datetime, permissions: dict,
                  snapshot_sha256: str, policy_sha256: str) -> dict:
    source_policy = policy["sources"]
    latest_by_zone = []
    stream_rows = []
    for source in snapshot.get("sources") or []:
        sid = source.get("sid")
        spec = source_policy.get(sid)
        if not spec or permissions.get(sid, {}).get("allowed") is not True:
            continue
        for stream in source.get("datastreams") or []:
            zone = spec["bindings"].get(stream.get("station"))
            if not zone:
                continue
            points = stream_points(sid, source, stream, cutoff)
            if not points:
                continue
            latest_by_zone.append({"zone": zone, "sid": sid, "domain": spec["domain"],
                                   "at": points[-1]["phenomenon_or_effective_time"]})
            if len(points) >= 2:
                stream_rows.append((source, stream, spec, zone, points))

    candidates = []
    for source, stream, spec, zone, points in stream_rows:
        latest = points[-1]
        latest_at = parse_time(latest["phenomenon_or_effective_time"])
        age_seconds = max(0, int((cutoff - latest_at).total_seconds()))
        fresh = age_seconds <= spec["maximum_age_minutes"] * 60
        cadence = spec["expected_cadence_seconds"]
        evidence = points[-3:]
        deltas = [evidence[i]["value"] - evidence[i - 1]["value"] for i in range(1, len(evidence))]
        gaps = [(parse_time(evidence[i]["phenomenon_or_effective_time"]) -
                 parse_time(evidence[i - 1]["phenomenon_or_effective_time"])).total_seconds()
                for i in range(1, len(evidence))]
        adjacent = len(evidence) == 3 and all(0 < gap <= cadence * 2.5 for gap in gaps)
        persistent = adjacent and deltas[0] != 0 and deltas[1] != 0 and (deltas[0] > 0) == (deltas[1] > 0)
        scale = max((abs(row["value"]) for row in evidence), default=0)
        uncertainty_reduction_ppm = round(abs(evidence[-1]["value"] - evidence[0]["value"]) / scale * 1_000_000) if scale else 0
        independent = sorted({row["domain"] for row in latest_by_zone
                              if row["zone"] == zone and row["sid"] != source["sid"]
                              and row["domain"] != spec["domain"]
                              and (cutoff - parse_time(row["at"])).total_seconds() <=
                              policy["signal"]["independent_domain_max_age_minutes"] * 60})
        verification = cadence <= policy["signal"]["maximum_verification_window_minutes"] * 60
        clock_rank = CLOCK_RANK[latest["clock"]]
        candidate = {
            "candidate_id": digest([source["sid"], stream.get("datastream"), zone, iso(cutoff)]),
            "sid": source["sid"],
            "stream": stream.get("datastream"),
            "zone": zone,
            "domain": spec["domain"],
            "property": stream.get("parameter"),
            "unit": stream.get("unit"),
            "permission": permissions[source["sid"]],
            "binding": {"method": policy["binding_method"], "evidence": policy["binding_evidence"],
                        "source_place": stream.get("station")},
            "clocks": {"phenomenon_or_effective": latest["phenomenon_or_effective_time"],
                       "published_or_result": latest["published_or_result_time"],
                       "received": latest["received_time"], "basis": latest["clock"]},
            "evidence": evidence,
            "change": {"deltas": deltas, "adjacent": adjacent,
                       "persistent_intervals": 2 if persistent else 0,
                       "direction": "up" if persistent and deltas[-1] > 0 else "down" if persistent else None},
            "independent_domains_present": independent,
            "age_seconds": age_seconds,
            "fresh": fresh,
            "next_check_within_two_hours": verification,
            "rank_vector": [1, clock_rank, 2 if persistent else 0, 1 if independent else 0,
                            -age_seconds, uncertainty_reduction_ppm],
            "uncertainty_reduction_proxy_ppm": uncertainty_reduction_ppm,
            "uncertainty_reduction_proxy_scope": "Three-point relative movement used only as a deterministic tie-break; not severity, trend or normality.",
            "eligible_for_proveri_sada": bool(fresh and persistent and verification),
            "known": "Poslednje tri uporedive tačke istog toka kreću se u istom smeru." if persistent else
                     "Tok ima najmanje dve uporedive tačke, ali nema dva susedna pomeranja u istom smeru.",
            "unknown": "Nije poznat uzrok niti da li će sledeća tačka zadržati smer; drugi domen nije potvrda signala.",
            "expected_observation": "Sledeća validna tačka istog toka proverava da li se isti smer nastavlja.",
            "falsifier": "Sledeća validna tačka menja smer, ostaje ista ili ne stiže u deklarisanom prozoru.",
        }
        candidates.append(candidate)

    candidates.sort(key=lambda row: tuple(-v for v in row["rank_vector"]) +
                    (str(row["sid"]), str(row["stream"])))
    accepted = [row for row in candidates if row["eligible_for_proveri_sada"]]
    if accepted:
        alternative, selected = "proveri_sada", accepted[0]
        rationale = "Prvi kandidat u preregistrovanom leksikografskom redu ima sve obavezne uslove."
    elif any(row["fresh"] for row in candidates):
        alternative, selected = "nastavi_pracenje", None
        rationale = "Postoji svež signal, ali nijedan tok nema dva susedna pomeranja istog smera i proveru u dva sata."
    else:
        alternative, selected = "nedovoljno_dokaza", None
        rationale = "Nema svežeg, prostorno vezanog i dozvoljenog toka sa dovoljno uporedivih tačaka."
    top_rank_tie_count = (sum(row["rank_vector"] == selected["rank_vector"] for row in candidates)
                          if selected else 0)
    candidate_count = len(candidates)
    candidate_set_sha256 = digest(candidates)
    retained_candidates = candidates[:policy.get("retain_ranked_candidates_per_episode", 12)]
    recheck_minutes = min(120, max(5, int(source_policy[selected["sid"]]["expected_cadence_seconds"] / 60))) if selected else 120
    payload = {
        "schema": "beops-d002-replay-episode/v1",
        "decision_id": "D-002",
        "frozen_at": iso(cutoff),
        "question": policy["question"],
        "scope": "Izbor naredne provere široke zone; bez gradske intervencije, uzroka, praga rizika ili mikrolokacijske tvrdnje.",
        "source_snapshot_sha256": snapshot_sha256,
        "policy_sha256": policy_sha256,
        "future_data_used": False,
        "ranking": policy["ranking"],
        "candidate_count": candidate_count,
        "candidate_set_sha256": candidate_set_sha256,
        "candidates": retained_candidates,
        "deterministic_result": {"alternative": alternative,
                                 "selected_candidate_id": selected["candidate_id"] if selected else None,
                                 "rationale": rationale,
                                 "top_rank_tie_count": top_rank_tie_count,
                                 "stable_id_tiebreak_used": top_rank_tie_count > 1},
        "human_decision": None,
        "ai_interpretation": None,
        "recheck_at": iso(cutoff + timedelta(minutes=recheck_minutes)),
        "outcome_due_at": iso(cutoff + timedelta(hours=24)),
        "outcome": None,
        "limits": policy["limits"],
    }
    payload["episode_id"] = digest(payload)
    return payload


def prepare_replay(root, snapshot_path, policy_path, output_path, count=10, spacing_minutes=120,
                   now=None, permissions_override=None) -> dict:
    root = pathlib.Path(root).resolve()
    snapshot_path, policy_path, output_path = map(lambda value: pathlib.Path(value).resolve(),
                                                  (snapshot_path, policy_path, output_path))
    for path in (snapshot_path, policy_path, output_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("D-002 paths must stay inside the project") from exc
    snapshot_raw, snapshot = read_bounded(snapshot_path, 64 * 1024 * 1024)
    policy_raw, policy = read_bounded(policy_path, 2 * 1024 * 1024)
    validate_policy(policy)
    as_of = parse_time(snapshot.get("as_of"))
    if snapshot.get("schema") != "beops-live-snapshot/v1" or not as_of:
        raise ValueError("invalid live snapshot")
    if not 1 <= count <= 50 or not 15 <= spacing_minutes <= 1440:
        raise ValueError("invalid replay window")
    now = now or datetime.now(timezone.utc)
    permissions = (permissions_override if permissions_override is not None
                   else permission_projection(root, policy, now))
    snapshot_sha, policy_sha = digest(snapshot_raw), digest(policy_raw)
    cutoffs = [as_of - timedelta(minutes=spacing_minutes * i) for i in reversed(range(count))]
    episodes = [build_episode(snapshot, policy, cutoff, permissions, snapshot_sha, policy_sha)
                for cutoff in cutoffs]
    result = {
        "schema": "beops-d002-replay-pack/v1",
        "state": "prepared_unreviewed",
        "prepared_at": iso(now),
        "policy_sha256": policy_sha,
        "source_snapshot": str(snapshot_path.relative_to(root)).replace("\\", "/"),
        "source_snapshot_sha256": snapshot_sha,
        "episodes": episodes,
        "episode_count": len(episodes),
        "future_outcomes_used": False,
        "human_decisions_complete": 0,
        "closed_outcomes": 0,
        "next": "Human review without changing the rule, then settle each outcome from evidence available after its frozen_at.",
    }
    result["pack_id"] = digest(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    fd = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        payload = raw.encode("utf-8")
        written = 0
        while written < len(payload):
            written += os.write(fd, payload[written:])
        os.fsync(fd)
    finally:
        os.close(fd)
    return {"output": str(output_path), "pack_id": result["pack_id"],
            "episodes": len(episodes),
            "alternatives": {name: sum(e["deterministic_result"]["alternative"] == name for e in episodes)
                             for name in policy["alternatives"]},
            "candidates_considered": sum(e["candidate_count"] for e in episodes),
            "candidates_retained": sum(len(e["candidates"]) for e in episodes)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--spacing-minutes", type=int, default=120)
    args = parser.parse_args()
    print(json.dumps(prepare_replay(args.root, args.snapshot, args.policy, args.output,
                                    args.count, args.spacing_minutes), ensure_ascii=False))


if __name__ == "__main__":
    main()
