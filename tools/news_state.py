"""Completion and attempt counts are derived from retained classifications; caches are never evidence."""
from collections import Counter

from contracts import json_rows, atomic_json


def complete(row, categories):
    return (row.get('state') == 'estimated' and row.get('category') in categories
            and isinstance(row.get('belgrade'), bool) and bool(row.get('input_key')))


def completed_keys(directory, categories):
    return {row['input_key'] for path in sorted(directory.glob('????-??.jsonl'))
            for row in json_rows(path) if complete(row, categories)}


def attempt_counts(directory):
    """Count only model rows that actually reached the append-only record.

    A transport timeout or malformed HTTP response has no row and therefore cannot
    consume a headline's semantic retry budget.
    """
    counts = Counter()
    for path in sorted(directory.glob('????-??.jsonl')):
        for row in json_rows(path):
            key = row.get('input_key')
            if isinstance(key, str) and key:
                counts[key] += 1
    return dict(sorted(counts.items()))


def reconcile(directory, categories, old_keys):
    keys = completed_keys(directory, categories)
    result = {'prior_cached': len(old_keys), 'supported_completed': len(keys),
              'unsupported_keys_removed': sorted(old_keys - keys),
              'supported_keys_recovered': sorted(keys - old_keys)}
    atomic_json(directory / '_done.json', sorted(keys))
    return result
