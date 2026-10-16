#!/usr/bin/env python3
"""Sample wiki notes for diagnostic audit passes.

The script is intentionally read-only by default. It can also update the
diagnostic ledger when asked to record completed audits or invalidate stale
issue fingerprints.
"""

import argparse
import hashlib
import json
import random
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VAULT_PATH = Path(__file__).resolve().parent.parent
WIKI_PATH = VAULT_PATH / "👾 Wiki"
DEFAULT_LEDGER_PATH = VAULT_PATH / ".scripts" / ".wiki_diagnostic_ledger.json"

EXCLUDED_NOTE_NAMES = {"AGENTS.md", "Index.md", "Log.md", "Questions.md"}
LINK_PATTERN = re.compile(r"\[\[([^\]|#\n]+?)(?:[#|][^\]\n]*)?\]\]")


class StrategyUnavailableError(RuntimeError):
    """Raised when a requested sampling strategy has no eligible notes."""


def timestamp_from_ns(timestamp_ns: int) -> str:
    """Render a filesystem timestamp as stable UTC text."""
    timestamp = datetime.fromtimestamp(timestamp_ns / 1_000_000_000, UTC)
    return timestamp.isoformat().replace("+00:00", "Z")


def now_timestamp() -> str:
    """Return the current UTC timestamp for ledger writes."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_ledger(ledger_path: Path) -> dict[str, Any]:
    """Read the diagnostic ledger, or return an empty schema if it is absent."""
    if not ledger_path.exists():
        return {"schema": 1, "note_audits": {}, "issues": {}}

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(ledger, dict):
        raise TypeError(f"Ledger must be a JSON object: {ledger_path}")

    if ledger.get("schema") != 1:
        raise ValueError(f"Unsupported ledger schema in {ledger_path}: {ledger.get('schema')}")

    if not isinstance(ledger.get("note_audits"), dict):
        raise TypeError(f"Ledger note_audits must be an object: {ledger_path}")

    if not isinstance(ledger.get("issues"), dict):
        raise TypeError(f"Ledger issues must be an object: {ledger_path}")

    return ledger


def save_ledger(ledger_path: Path, ledger: dict[str, Any]) -> None:
    """Persist the diagnostic ledger with stable formatting."""
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_note_records(wiki_path: Path) -> dict[str, dict[str, Any]]:
    """Load wiki note metadata needed for sampling and invalidation."""
    if not wiki_path.exists():
        raise FileNotFoundError(f"Wiki directory does not exist: {wiki_path}")

    records: dict[str, dict[str, Any]] = {}
    for note_path in sorted(wiki_path.glob("*.md")):
        if note_path.name in EXCLUDED_NOTE_NAMES:
            continue

        stat_result = note_path.stat()
        title = note_path.stem
        records[title] = {
            "title": title,
            "path": str(note_path),
            "updated_at_ns": stat_result.st_mtime_ns,
            "updated_at": timestamp_from_ns(stat_result.st_mtime_ns),
            "outbound_degree": 0,
            "inbound_degree": 0,
        }

    if not records:
        raise ValueError(f"No eligible wiki notes found in {wiki_path}")

    return records


def add_graph_degrees(note_records: dict[str, dict[str, Any]]) -> None:
    """Compute simple inbound and outbound wiki-link degrees for every note."""
    titles = set(note_records)

    for source_title, source_record in note_records.items():
        text = Path(source_record["path"]).read_text(encoding="utf-8")
        targets = set()

        for match in LINK_PATTERN.finditer(text):
            target_title = match.group(1).strip()
            if target_title in titles and target_title != source_title:
                targets.add(target_title)

        source_record["outbound_degree"] = len(targets)
        for target_title in targets:
            note_records[target_title]["inbound_degree"] += 1


def invalidate_stale_issues(
    ledger: dict[str, Any],
    note_records: dict[str, dict[str, Any]],
    invalidated_at: str,
) -> list[dict[str, Any]]:
    """Mark issue fingerprints stale when any referenced note changed later."""
    invalidated_issues: list[dict[str, Any]] = []
    issues = ledger["issues"]

    for fingerprint, issue in issues.items():
        if not isinstance(issue, dict):
            raise TypeError(f"Issue entry must be an object: {fingerprint}")

        if issue.get("status") == "invalidated":
            continue

        note_timestamps = issue.get("note_timestamps")
        if not isinstance(note_timestamps, dict):
            raise TypeError(f"Issue note_timestamps must be an object: {fingerprint}")

        invalidated_by: list[str] = []
        for title, recorded_timestamp in note_timestamps.items():
            if title not in note_records:
                invalidated_by.append(title)
                continue

            if not isinstance(recorded_timestamp, dict):
                raise TypeError(f"Issue timestamp entry must be an object: {fingerprint} / {title}")

            recorded_updated_at_ns = recorded_timestamp.get("updated_at_ns")
            if not isinstance(recorded_updated_at_ns, int):
                raise TypeError(f"Issue updated_at_ns must be an integer: {fingerprint} / {title}")

            current_updated_at_ns = note_records[title]["updated_at_ns"]
            if current_updated_at_ns > recorded_updated_at_ns:
                invalidated_by.append(title)

        if not invalidated_by:
            continue

        issue["previous_status"] = issue.get("status")
        issue["status"] = "invalidated"
        issue["invalidated_at"] = invalidated_at
        issue["invalidated_by"] = sorted(invalidated_by)
        invalidated_issues.append({"fingerprint": fingerprint, "invalidated_by": sorted(invalidated_by)})

    return invalidated_issues


def current_audit_exists(note_record: dict[str, Any], audit_record: dict[str, Any] | None) -> bool:
    """Return whether the ledger audit still covers the current note content."""
    if audit_record is None:
        return False

    audited_updated_at_ns = audit_record.get("updated_at_ns")
    if not isinstance(audited_updated_at_ns, int):
        return False

    return audited_updated_at_ns >= note_record["updated_at_ns"]


def weighted_sample_without_replacement(
    titles: list[str],
    weights_by_title: dict[str, float],
    count: int,
    random_generator: random.Random,
) -> list[str]:
    """Sample titles without replacement using positive weights."""
    remaining_titles = list(titles)
    selected_titles: list[str] = []

    while remaining_titles and len(selected_titles) < count:
        total_weight = sum(weights_by_title[title] for title in remaining_titles)
        if total_weight <= 0:
            raise ValueError("Sampling weights must sum to a positive value")

        threshold = random_generator.random() * total_weight
        cumulative_weight = 0.0

        for title in remaining_titles:
            cumulative_weight += weights_by_title[title]
            if cumulative_weight >= threshold:
                selected_titles.append(title)
                remaining_titles.remove(title)
                break

    if len(selected_titles) < count:
        raise StrategyUnavailableError(f"Only {len(selected_titles)} eligible notes for count={count}")

    return selected_titles


def sample_random(
    note_records: dict[str, dict[str, Any]],
    count: int,
    random_generator: random.Random,
) -> list[str]:
    """Sample uniformly from all eligible notes."""
    titles = sorted(note_records)
    if count > len(titles):
        raise StrategyUnavailableError(f"Only {len(titles)} eligible notes for count={count}")

    return random_generator.sample(titles, count)


def sample_unaudited(
    note_records: dict[str, dict[str, Any]],
    ledger: dict[str, Any],
    count: int,
    random_generator: random.Random,
) -> list[str]:
    """Prefer notes with no current audit record."""
    audit_records = ledger["note_audits"]
    unaudited_titles = [
        title
        for title, note_record in note_records.items()
        if not current_audit_exists(note_record, audit_records.get(title))
    ]

    if len(unaudited_titles) >= count:
        return random_generator.sample(sorted(unaudited_titles), count)

    ranked_titles = sorted(
        note_records,
        key=lambda title: audit_records.get(title, {}).get("audited_at", ""),
    )
    return ranked_titles[:count]


def sample_high_degree(
    note_records: dict[str, dict[str, Any]],
    count: int,
    random_generator: random.Random,
) -> list[str]:
    """Sample notes weighted by local graph degree."""
    titles = sorted(note_records)
    weights_by_title = {
        title: 1.0 + note_record["outbound_degree"] + note_record["inbound_degree"]
        for title, note_record in note_records.items()
    }
    return weighted_sample_without_replacement(titles, weights_by_title, count, random_generator)


def sample_recently_edited(
    note_records: dict[str, dict[str, Any]],
    count: int,
    random_generator: random.Random,
) -> list[str]:
    """Sample from the most recently edited slice of the wiki."""
    ranked_titles = sorted(
        note_records,
        key=lambda title: note_records[title]["updated_at_ns"],
        reverse=True,
    )
    pool_size = min(len(ranked_titles), max(20, count * 5))
    recent_titles = ranked_titles[:pool_size]
    if count > len(recent_titles):
        raise StrategyUnavailableError(f"Only {len(recent_titles)} recent notes for count={count}")

    return random_generator.sample(recent_titles, count)


def active_issue_note_titles(ledger: dict[str, Any], note_records: dict[str, dict[str, Any]]) -> list[str]:
    """Return note titles attached to unresolved, non-stale issue fingerprints."""
    titles: set[str] = set()
    active_statuses = {"open", "reported", "accepted", "intentional-tension"}

    for issue in ledger["issues"].values():
        if not isinstance(issue, dict):
            raise TypeError("Issue entries must be objects")

        if issue.get("status") not in active_statuses:
            continue

        issue_titles = issue.get("notes")
        if not isinstance(issue_titles, list):
            raise TypeError("Issue notes must be a list")

        for title in issue_titles:
            if title in note_records:
                titles.add(title)

    return sorted(titles)


def sample_unresolved(
    note_records: dict[str, dict[str, Any]],
    ledger: dict[str, Any],
    count: int,
    random_generator: random.Random,
) -> list[str]:
    """Sample from notes attached to unresolved issue fingerprints."""
    titles = active_issue_note_titles(ledger, note_records)
    if len(titles) < count:
        raise StrategyUnavailableError(f"Only {len(titles)} unresolved issue notes for count={count}")

    return random_generator.sample(titles, count)


def sample_mixed(
    note_records: dict[str, dict[str, Any]],
    ledger: dict[str, Any],
    count: int,
    random_generator: random.Random,
) -> list[str]:
    """Sample using the 40/25/20/15 mixed diagnostic policy."""
    selected_titles: list[str] = []
    strategy_weights = {
        "unaudited": 40,
        "high-degree": 25,
        "recently-edited": 20,
        "unresolved": 15,
    }

    while len(selected_titles) < count:
        available_strategies: list[str] = []
        available_weights: dict[str, float] = {}

        for strategy, weight in strategy_weights.items():
            candidates = sample_by_strategy(
                strategy,
                note_records,
                ledger,
                1,
                random_generator,
                allow_partial=True,
            )
            candidates = [title for title in candidates if title not in selected_titles]
            if not candidates:
                continue

            available_strategies.append(strategy)
            available_weights[strategy] = float(weight)

        if not available_strategies:
            raise StrategyUnavailableError(f"Only {len(selected_titles)} eligible notes for count={count}")

        selected_strategy = weighted_sample_without_replacement(
            available_strategies,
            available_weights,
            1,
            random_generator,
        )[0]
        selected_title = sample_by_strategy(
            selected_strategy,
            note_records,
            ledger,
            1,
            random_generator,
            allow_partial=False,
            excluded_titles=set(selected_titles),
        )[0]
        selected_titles.append(selected_title)

    return selected_titles


def sample_by_strategy(
    strategy: str,
    note_records: dict[str, dict[str, Any]],
    ledger: dict[str, Any],
    count: int,
    random_generator: random.Random,
    allow_partial: bool = False,
    excluded_titles: set[str] | None = None,
) -> list[str]:
    """Dispatch a sampling strategy and optionally remove already selected notes."""
    if excluded_titles is None:
        excluded_titles = set()

    filtered_records = {
        title: note_record
        for title, note_record in note_records.items()
        if title not in excluded_titles
    }

    if not filtered_records:
        if allow_partial:
            return []
        raise StrategyUnavailableError("No eligible notes after exclusions")

    try:
        if strategy == "random":
            return sample_random(filtered_records, count, random_generator)
        if strategy == "unaudited":
            return sample_unaudited(filtered_records, ledger, count, random_generator)
        if strategy == "high-degree":
            return sample_high_degree(filtered_records, count, random_generator)
        if strategy == "recently-edited":
            return sample_recently_edited(filtered_records, count, random_generator)
        if strategy == "unresolved":
            return sample_unresolved(filtered_records, ledger, count, random_generator)
        if strategy == "mixed":
            return sample_mixed(filtered_records, ledger, count, random_generator)
    except StrategyUnavailableError:
        if allow_partial:
            return []
        raise

    raise ValueError(f"Unknown strategy: {strategy}")


def record_audits(
    ledger: dict[str, Any],
    note_records: dict[str, dict[str, Any]],
    titles: list[str],
    strategy: str,
    audited_at: str,
) -> list[dict[str, Any]]:
    """Record completed audits for explicit note titles."""
    records: list[dict[str, Any]] = []

    for title in titles:
        if title not in note_records:
            raise KeyError(f"Cannot record audit for unknown note: {title}")

        note_record = note_records[title]
        audit_record = {
            "audited_at": audited_at,
            "path": note_record["path"],
            "strategy": strategy,
            "updated_at": note_record["updated_at"],
            "updated_at_ns": note_record["updated_at_ns"],
        }
        ledger["note_audits"][title] = audit_record
        records.append({"title": title, **audit_record})

    return records


def normalize_claim_fragment(claim_fragment: str) -> str:
    """Normalize a claim fragment before fingerprinting."""
    return " ".join(claim_fragment.casefold().split())


def build_issue_fingerprint(issue_type: str, titles: list[str], claim_fragment: str) -> str:
    """Build a stable fingerprint independent of note update timestamps."""
    payload = {
        "claim_fragment": normalize_claim_fragment(claim_fragment),
        "issue_type": issue_type,
        "notes": sorted(titles),
    }
    payload_text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload_text.encode("utf-8")).hexdigest()


def record_issue(
    ledger: dict[str, Any],
    note_records: dict[str, dict[str, Any]],
    issue_type: str,
    status: str,
    titles: list[str],
    claim_fragment: str,
    summary: str,
    recorded_at: str,
) -> dict[str, Any]:
    """Record or refresh an issue fingerprint with current note timestamps."""
    unique_titles = sorted(set(titles))
    for title in unique_titles:
        if title not in note_records:
            raise KeyError(f"Cannot record issue for unknown note: {title}")

    fingerprint = build_issue_fingerprint(issue_type, unique_titles, claim_fragment)
    note_timestamps = {
        title: {
            "updated_at": note_records[title]["updated_at"],
            "updated_at_ns": note_records[title]["updated_at_ns"],
        }
        for title in unique_titles
    }

    issue_record = {
        "claim_fragment": claim_fragment,
        "first_reported_at": recorded_at,
        "issue_type": issue_type,
        "last_reported_at": recorded_at,
        "note_timestamps": note_timestamps,
        "notes": unique_titles,
        "status": status,
        "summary": summary,
    }

    existing_issue = ledger["issues"].get(fingerprint)
    if isinstance(existing_issue, dict) and existing_issue.get("first_reported_at"):
        issue_record["first_reported_at"] = existing_issue["first_reported_at"]

    ledger["issues"][fingerprint] = issue_record
    return {"fingerprint": fingerprint, **issue_record}


def build_sample_output(
    strategy: str,
    titles: list[str],
    note_records: dict[str, dict[str, Any]],
    invalidated_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the JSON-serializable command output."""
    samples = []
    for title in titles:
        note_record = note_records[title]
        samples.append(
            {
                "title": title,
                "path": note_record["path"],
                "updated_at": note_record["updated_at"],
                "updated_at_ns": note_record["updated_at_ns"],
                "outbound_degree": note_record["outbound_degree"],
                "inbound_degree": note_record["inbound_degree"],
                "total_degree": note_record["outbound_degree"] + note_record["inbound_degree"],
            }
        )

    return {
        "strategy": strategy,
        "samples": samples,
        "invalidated_issues": invalidated_issues,
    }


def print_text_output(output: dict[str, Any]) -> None:
    """Print a human-readable sampling report."""
    print(f"Strategy: {output['strategy']}")

    if output["invalidated_issues"]:
        print("Invalidated fingerprints:")
        for issue in output["invalidated_issues"]:
            notes = ", ".join(issue["invalidated_by"])
            print(f"  {issue['fingerprint']} ({notes})")

    print("Samples:")
    for sample in output["samples"]:
        print(f"  [[{sample['title']}]]")
        print(f"    path: {sample['path']}")
        print(f"    updated_at: {sample['updated_at']}")
        print(f"    degree: {sample['total_degree']} ({sample['outbound_degree']} out, {sample['inbound_degree']} in)")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Sample wiki notes for diagnostic audit passes.")
    parser.add_argument("--vault", type=Path, default=VAULT_PATH, help="Vault root path.")
    parser.add_argument("--wiki", type=Path, default=None, help="Wiki directory path.")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER_PATH, help="Diagnostic ledger JSON path.")
    parser.add_argument(
        "--strategy",
        choices=["random", "unaudited", "high-degree", "recently-edited", "unresolved", "mixed"],
        default="mixed",
        help="Sampling strategy.",
    )
    parser.add_argument("--count", type=int, default=1, help="Number of notes to sample.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible sampling.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    parser.add_argument("--update-ledger", action="store_true", help="Write stale fingerprint invalidations to the ledger.")
    parser.add_argument("--invalidate-only", action="store_true", help="Invalidate stale fingerprints and exit without sampling.")
    parser.add_argument(
        "--record-audit",
        action="append",
        default=[],
        help="Record a completed audit for this note title. Can be repeated.",
    )
    parser.add_argument("--record-issue", action="store_true", help="Record an issue fingerprint and write the ledger.")
    parser.add_argument("--issue-type", default=None, help="Issue type for --record-issue.")
    parser.add_argument("--issue-status", default="reported", help="Issue status for --record-issue.")
    parser.add_argument("--issue-note", action="append", default=[], help="Note title involved in --record-issue.")
    parser.add_argument("--issue-claim", default=None, help="Normalized claim fragment for --record-issue.")
    parser.add_argument("--issue-summary", default="", help="Short human-readable issue summary.")
    return parser.parse_args()


def main() -> int:
    """Run the sampler."""
    arguments = parse_arguments()
    if arguments.count < 1:
        raise ValueError("--count must be at least 1")

    wiki_path = arguments.wiki
    if wiki_path is None:
        wiki_path = arguments.vault / "👾 Wiki"

    random_generator = random.Random(arguments.seed)
    ledger = load_ledger(arguments.ledger)
    note_records = load_note_records(wiki_path)
    add_graph_degrees(note_records)

    timestamp = now_timestamp()
    invalidated_issues = invalidate_stale_issues(ledger, note_records, timestamp)

    if arguments.invalidate_only:
        if invalidated_issues or arguments.update_ledger:
            save_ledger(arguments.ledger, ledger)

        print(json.dumps({"invalidated_issues": invalidated_issues}, indent=2))
        return 0

    if arguments.record_audit:
        records = record_audits(ledger, note_records, arguments.record_audit, arguments.strategy, timestamp)
        save_ledger(arguments.ledger, ledger)
        print(json.dumps({"recorded_audits": records, "invalidated_issues": invalidated_issues}, indent=2))
        return 0

    if arguments.record_issue:
        if arguments.issue_type is None:
            raise ValueError("--issue-type is required with --record-issue")
        if arguments.issue_claim is None:
            raise ValueError("--issue-claim is required with --record-issue")
        if not arguments.issue_note:
            raise ValueError("--issue-note is required with --record-issue")

        issue = record_issue(
            ledger,
            note_records,
            arguments.issue_type,
            arguments.issue_status,
            arguments.issue_note,
            arguments.issue_claim,
            arguments.issue_summary,
            timestamp,
        )
        save_ledger(arguments.ledger, ledger)
        print(json.dumps({"recorded_issue": issue, "invalidated_issues": invalidated_issues}, indent=2))
        return 0

    sample_titles = sample_by_strategy(arguments.strategy, note_records, ledger, arguments.count, random_generator)

    if arguments.update_ledger and invalidated_issues:
        save_ledger(arguments.ledger, ledger)

    output = build_sample_output(arguments.strategy, sample_titles, note_records, invalidated_issues)
    if arguments.format == "json":
        print(json.dumps(output, indent=2))
        return 0

    print_text_output(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, TypeError, ValueError, StrategyUnavailableError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
