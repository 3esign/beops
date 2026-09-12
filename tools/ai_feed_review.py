"""Freeze and score a blinded review of durable Beops AI-feed responses.

Only attempts with an immutable response, context and prompt enter text-quality
review. Provider failures, timeouts and capacity deferrals remain visible in the
population counts but never masquerade as bad prose. No model is called.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone

from contracts import atomic_json, json_object


CRITERIA = (
    "evidence_support",
    "precision",
    "novelty_above_control",
    "usefulness_above_control",
    "adequate_guardrail",
    "causal_error",
)
RATINGS = {"yes", "no", "uncertain"}


def canonical_digest(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def text(value) -> str:
    return str(value).replace("\x00", " ").strip()


def deterministic_control(context: dict) -> dict:
    """Describe supplied facts without inference, thresholds or causal language."""
    facts = []
    for fact in context.get("facts", []):
        fid = text(fact.get("id") or "?")
        source = text(fact.get("source") or fact.get("sid") or "neimenovan izvor")
        if fact.get("kind") == "observation":
            place = text(fact.get("place") or "nepoznata zona")
            metric = text(fact.get("metric") or fact.get("stream") or "vrednost")
            value = fact.get("value")
            unit = text(fact.get("unit") or "")
            clock = text(fact.get("clock") or "nepoznat sat")
            when = text(fact.get("time") or "nepoznato vreme")
            received = text(fact.get("received_at") or "nepoznato")
            line = f"{fid}: {source}; {place}; {metric} = {value}{(' ' + unit) if unit else ''}; {clock} {when}; primljeno {received}."
            comparison = fact.get("comparison") or {}
            if comparison:
                line += (f" Prethodno {comparison.get('from_value')} u {text(comparison.get('from_time'))}; "
                         f"razlika {comparison.get('delta')}.")
        else:
            keep = []
            for key in ("dataset_id", "title", "territory", "territory_id", "period", "value", "unit"):
                if fact.get(key) not in (None, ""):
                    keep.append(f"{key}={fact[key]}")
            line = f"{fid}: {source}; " + ("; ".join(keep) if keep else "istorijski kontekst bez dodatog tumačenja") + "."
        facts.append(line)
    coverage = context.get("coverage") or []
    missing = []
    for row in coverage:
        seen, usable = row.get("observed_streams"), row.get("usable_streams")
        if isinstance(seen, int) and isinstance(usable, int) and usable < seen:
            missing.append(f"{row.get('sid', '?')}: upotrebljivo {usable}/{seen} tokova")
    return {
        "schema": "beops-deterministic-control/v1",
        "as_of": context.get("as_of"),
        "facts": facts,
        "missing": missing,
        "limitation": "Ovaj presek opisuje samo navedene izvore i vremena; ne dokazuje uzrok, dugoročni trend, stanje cele zone niti zdravstveni ili regulatorni zaključak.",
    }


def terminal_receipts(directory: pathlib.Path) -> dict[str, dict]:
    out = {}
    for path in sorted((directory / "receipts").glob("*-finish.json")):
        row = json_object(path)
        attempt = text(row.get("id"))
        if not attempt or attempt in out:
            raise ValueError("missing or duplicate terminal attempt id")
        out[attempt] = row
    return out


def verified_candidate(directory: pathlib.Path, attempt: str, finish: dict) -> dict:
    response_path = directory / "responses" / f"{attempt}.json"
    context_hash, prompt_hash = finish.get("context_hash"), finish.get("prompt_hash")
    if not all(isinstance(v, str) and len(v) == 64 for v in (context_hash, prompt_hash)):
        raise ValueError(f"attempt {attempt} has no complete input hashes")
    context_path = directory / "contexts" / f"{context_hash}.json"
    prompt_path = directory / "prompts" / f"{prompt_hash}.txt"
    for expected, path in ((context_hash, context_path), (prompt_hash, prompt_path)):
        if not path.is_file() or file_digest(path) != expected:
            raise ValueError(f"attempt {attempt} has missing or mismatched {path.parent.name}")
    response = json_object(response_path)
    output = response.get("text")
    if not isinstance(output, str) or not output.strip():
        raise ValueError(f"attempt {attempt} has an empty response")
    context = json_object(context_path)
    entry_path = directory / "entries" / f"{attempt}.json"
    accepted = finish.get("state") == "accepted"
    entry = json_object(entry_path) if entry_path.exists() else None
    if accepted and (entry is None or entry.get("context_hash") != context_hash or entry.get("prompt_hash") != prompt_hash):
        raise ValueError(f"accepted attempt {attempt} has no matching entry")
    if not accepted and entry is not None:
        raise ValueError(f"non-accepted attempt {attempt} has a public entry")
    response_sha = file_digest(response_path)
    return {
        "id": canonical_digest(["beops-ai-review", attempt])[:24],
        "context_hash": context_hash,
        "prompt_hash": prompt_hash,
        "response_sha256": response_sha,
        "chain_sha256": canonical_digest([context_hash, prompt_hash, response_sha]),
        "output_text": output,
        "context": context,
        "deterministic_control": deterministic_control(context),
        "private_attempt_id": attempt,
        "private_provider": finish.get("provider"),
        "private_model": finish.get("model"),
        "private_terminal_state": finish.get("state"),
        "private_terminal_reason": finish.get("reason"),
        "private_validation": finish.get("validation"),
        "private_response": response,
        "private_entry": entry,
    }


def round_robin(rows: list[dict], limit: int, seed: str) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[(text(row.get("private_provider")), text(row.get("private_terminal_reason")))].append(row)
    for group in groups.values():
        group.sort(key=lambda row: canonical_digest([seed, row["id"], "sample"]))
    chosen = []
    while len(chosen) < limit and any(groups.values()):
        for key in sorted(groups):
            if groups[key] and len(chosen) < limit:
                chosen.append(groups[key].pop())
    return chosen


def blinded(packet: dict) -> dict:
    return {
        "schema": "beops-ai-blind-review/v1",
        "packet_id": packet["packet_id"],
        "frozen_at": packet["frozen_at"],
        "target_size": packet["target_size"],
        "selected_size": packet["selected_size"],
        "sample_state": packet["sample_state"],
        "shortage": packet["shortage"],
        "criteria": list(CRITERIA),
        "rows": [{k: v for k, v in row.items() if not k.startswith("private_")}
                 for row in packet["rows"]],
    }


def prepare(source, output, target=60, seed="beops-ai-quality-20260912") -> dict:
    source, output = pathlib.Path(source).resolve(), pathlib.Path(output).resolve()
    if output.exists():
        raise FileExistsError("review output already exists; preserve the frozen packet")
    if target < 1 or target > 500:
        raise ValueError("target must be between 1 and 500")
    directory = source / "runtime" / "ai-feed"
    finishes = terminal_receipts(directory)
    response_ids = {path.stem for path in (directory / "responses").glob("*.json")}
    orphan_responses = sorted(response_ids - set(finishes))
    if orphan_responses:
        raise ValueError("response without terminal receipt")
    candidates, excluded = [], Counter()
    states, reasons = Counter(), Counter()
    for attempt, finish in finishes.items():
        state = text(finish.get("state") or "unknown")
        states[state] += 1
        if finish.get("reason"):
            reasons[text(finish["reason"])] += 1
        if attempt not in response_ids:
            excluded[f"no_response:{state}"] += 1
            continue
        if state not in {"accepted", "failed"}:
            excluded[f"response_with_terminal:{state}"] += 1
            continue
        candidates.append(verified_candidate(directory, attempt, finish))
    accepted = [row for row in candidates if row["private_terminal_state"] == "accepted"]
    rejected = [row for row in candidates if row["private_terminal_state"] == "failed"]
    accepted.sort(key=lambda row: canonical_digest([seed, row["id"], "accepted"]))
    if len(accepted) >= target:
        selected = accepted[:target]
    else:
        selected = accepted + round_robin(rejected, target - len(accepted), seed)
    selected.sort(key=lambda row: canonical_digest([seed, row["id"], "display"]))
    frozen_at = datetime.now(timezone.utc).isoformat()
    packet = {
        "schema": "beops-ai-quality-packet/v1",
        "frozen_at": frozen_at,
        "seed": seed,
        "target_size": target,
        "selected_size": len(selected),
        "sample_state": "ready_for_review" if len(selected) >= target else "insufficient_sample",
        "shortage": max(0, target - len(selected)),
        "population": {
            "terminal_attempts": len(finishes),
            "states": dict(sorted(states.items())),
            "reasons": dict(sorted(reasons.items())),
            "responses": len(response_ids),
            "accepted_responses": len(accepted),
            "rejected_responses": len(rejected),
            "excluded": dict(sorted(excluded.items())),
        },
        "scope": "Frozen diagnostic population of durable textual responses; operational attempts without a response are counted separately and are not quality examples.",
        "rows": selected,
    }
    packet["packet_id"] = canonical_digest(packet)
    template = pathlib.Path(__file__).with_name("ai_feed_review.html").read_text(encoding="utf-8")
    blind = blinded(packet)
    parent = output.parent
    parent.mkdir(parents=True, exist_ok=True)
    temporary = pathlib.Path(tempfile.mkdtemp(prefix=".ai-quality-", dir=parent))
    try:
        atomic_json(temporary / "packet-private.json", packet)
        atomic_json(temporary / "packet-blind.json", blind)
        embedded = json.dumps(blind, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        (temporary / "review.html").write_text(template.replace("__PACKET__", embedded), encoding="utf-8", newline="\n")
        atomic_json(temporary / "status.json", {
            "schema": "beops-ai-quality-status/v1",
            "packet_id": packet["packet_id"],
            "state": packet["sample_state"],
            "items": len(selected),
            "target": target,
            "shortage": packet["shortage"],
            "human_annotations": 0,
        })
        os.replace(temporary, output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {
        "output": str(output),
        "packet_id": packet["packet_id"],
        "state": packet["sample_state"],
        "items": len(selected),
        "shortage": packet["shortage"],
        "population": packet["population"],
    }


def validate_annotations(packet: dict, annotations: dict) -> dict[str, dict]:
    if annotations.get("packet_id") != packet.get("packet_id"):
        raise ValueError("annotations belong to a different packet")
    if annotations.get("reviewer_type") != "human" or not text(annotations.get("reviewer")):
        raise ValueError("an identified human reviewer is required")
    if annotations.get("independent_before_reveal") is not True:
        raise ValueError("independent annotation before reveal is required")
    known = {row["id"] for row in packet["rows"]}
    out = {}
    for label in annotations.get("rows", []):
        key = label.get("id")
        if key not in known or key in out:
            raise ValueError("unknown or duplicate annotation id")
        ratings = label.get("ratings")
        if not isinstance(ratings, dict) or set(ratings) != set(CRITERIA):
            raise ValueError("every completed annotation needs the full rubric")
        if any(value not in RATINGS for value in ratings.values()):
            raise ValueError("invalid rubric rating")
        out[key] = label
    return out


def score(packet: dict, annotations: dict) -> dict:
    labels = validate_annotations(packet, annotations)
    rows = {row["id"]: row for row in packet["rows"]}
    metrics = {}
    for criterion in CRITERIA:
        values = [label["ratings"][criterion] for label in labels.values()]
        decidable = [value for value in values if value != "uncertain"]
        metrics[criterion] = {
            "annotated": len(values),
            "decidable": len(decidable),
            "yes": sum(value == "yes" for value in decidable),
            "no": sum(value == "no" for value in decidable),
            "yes_rate": (sum(value == "yes" for value in decidable) / len(decidable)) if decidable else None,
        }
    accepted = [(rows[key], label) for key, label in labels.items()
                if rows[key]["private_terminal_state"] == "accepted"]
    hard_failures = {
        "unsupported": sum(label["ratings"]["evidence_support"] == "no" for _, label in accepted),
        "causal_error": sum(label["ratings"]["causal_error"] == "yes" for _, label in accepted),
        "missing_guardrail": sum(label["ratings"]["adequate_guardrail"] == "no" for _, label in accepted),
    }
    return {
        "schema": "beops-ai-quality-result/v1",
        "packet_id": packet["packet_id"],
        "reviewer": annotations["reviewer"],
        "state": "complete" if len(labels) == len(rows) and rows else "partial",
        "annotated": len(labels),
        "expected": len(rows),
        "metrics": metrics,
        "accepted_decisions": len(accepted),
        "accepted_hard_failures": hard_failures,
        "scope": "Human evidence judgment on this frozen sample; uncertain ratings stay outside each decidable denominator.",
    }


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    observed = sum(a == b for a, b in pairs) / len(pairs)
    pa = sum(a == "yes" for a, _ in pairs) / len(pairs)
    pb = sum(b == "yes" for _, b in pairs) / len(pairs)
    expected = pa * pb + (1 - pa) * (1 - pb)
    if expected == 1:
        return 1.0 if observed == 1 else None
    return (observed - expected) / (1 - expected)


def compare(packet: dict, first: dict, second: dict) -> dict:
    a, b = validate_annotations(packet, first), validate_annotations(packet, second)
    if text(first.get("reviewer")) == text(second.get("reviewer")):
        raise ValueError("two distinct human reviewers are required")
    overlap = sorted(set(a) & set(b))
    metrics = {}
    for criterion in CRITERIA:
        pairs = [(a[key]["ratings"][criterion], b[key]["ratings"][criterion]) for key in overlap
                 if "uncertain" not in (a[key]["ratings"][criterion], b[key]["ratings"][criterion])]
        metrics[criterion] = {
            "decidable_overlap": len(pairs),
            "agreement": (sum(x == y for x, y in pairs) / len(pairs)) if pairs else None,
            "kappa": kappa(pairs),
        }
    return {
        "schema": "beops-ai-quality-agreement/v1",
        "packet_id": packet["packet_id"],
        "reviewers": [first["reviewer"], second["reviewer"]],
        "overlap": len(overlap),
        "target_overlap": 20,
        "state": "complete" if len(overlap) >= 20 else "insufficient_overlap",
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("prepare")
    make.add_argument("--source", required=True)
    make.add_argument("--output", required=True)
    make.add_argument("--target", type=int, default=60)
    make.add_argument("--seed", default="beops-ai-quality-20260912")
    one = commands.add_parser("score")
    one.add_argument("--packet", required=True)
    one.add_argument("--annotations", required=True)
    one.add_argument("--output", required=True)
    two = commands.add_parser("compare")
    two.add_argument("--packet", required=True)
    two.add_argument("--first", required=True)
    two.add_argument("--second", required=True)
    two.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.source, args.output, args.target, args.seed)
    else:
        output = pathlib.Path(args.output)
        if output.exists():
            raise FileExistsError("result already exists; preserve the earlier result")
        packet = json_object(pathlib.Path(args.packet))
        if args.command == "score":
            result = score(packet, json_object(pathlib.Path(args.annotations)))
        else:
            result = compare(packet, json_object(pathlib.Path(args.first)),
                             json_object(pathlib.Path(args.second)))
        atomic_json(output, result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
