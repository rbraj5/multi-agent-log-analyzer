from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = {
    "web": ROOT / "sample_data/web.log",
    "database": ROOT / "sample_data/database.log",
    "auth": ROOT / "sample_data/auth.log",
}
LEVEL_SCORE = {"WARNING": 2, "ERROR": 4, "CRITICAL": 5}


@dataclass
class LogIssue:
    level: str
    message: str
    count: int
    severity: int
    likely_cause: str
    remediation: str


def parse_issue_line(line: str) -> tuple[str, str] | None:
    match = re.search(r"\b(WARNING|ERROR|CRITICAL)\b\s+(.*)", line)
    if not match:
        return None
    return match.group(1), match.group(2).strip()


def log_parser(log_text: str) -> list[tuple[str, str]]:
    issues = []
    for line in log_text.splitlines():
        parsed = parse_issue_line(line)
        if parsed:
            issues.append(parsed)
    return issues


def infer_cause(message: str) -> str:
    lowered = message.lower()
    if "timeout" in lowered:
        return "A dependency is slow or unavailable."
    if "pool exhausted" in lowered or "connection" in lowered:
        return "The service may be running out of available connections."
    if "deadlock" in lowered:
        return "Concurrent database transactions are blocking each other."
    if "failed login" in lowered or "suspicious" in lowered or "locked" in lowered:
        return "Authentication traffic suggests repeated failed access attempts."
    if "latency" in lowered or "slow query" in lowered:
        return "Performance degradation is visible before the failure."
    if "failure rate" in lowered:
        return "The user-facing path has crossed an operational failure threshold."
    return "The issue needs review with surrounding logs and recent deployments."


def recommend_fix(message: str) -> str:
    lowered = message.lower()
    if "timeout" in lowered:
        return "Check dependency health, increase observability around latency, and add retry/backoff limits."
    if "pool exhausted" in lowered:
        return "Inspect connection leaks, tune pool size, and review long-running requests."
    if "deadlock" in lowered:
        return "Review transaction ordering, indexes, and retry logic for affected operations."
    if "failed login" in lowered or "suspicious" in lowered or "locked" in lowered:
        return "Rate-limit attempts, verify alerts, and review account/IP activity."
    if "slow query" in lowered:
        return "Run query analysis, add indexes where appropriate, and check table growth."
    return "Capture more context, assign an owner, and validate the fix in a lower environment."


def issue_investigator(parsed_issues: list[tuple[str, str]]) -> list[LogIssue]:
    grouped = Counter(parsed_issues)
    investigated = []
    for (level, message), count in grouped.most_common():
        severity = min(5, LEVEL_SCORE[level] + (1 if count > 1 else 0))
        investigated.append(
            LogIssue(
                level=level,
                message=message,
                count=count,
                severity=severity,
                likely_cause=infer_cause(message),
                remediation=recommend_fix(message),
            )
        )
    return investigated


def fix_recommender(issues: list[LogIssue]) -> str:
    if not issues:
        return "# Log Analysis Report\n\nNo warning, error, or critical log entries were found."

    lines = [
        "# Log Analysis Report",
        "",
        "## Issue Triage",
        "| Level | Count | Severity | Message |",
        "| --- | ---: | ---: | --- |",
    ]
    for issue in issues:
        lines.append(f"| {issue.level} | {issue.count} | {issue.severity} | {issue.message} |")

    lines.extend(["", "## Root Cause Notes"])
    for issue in issues:
        lines.append(f"- **{issue.message}**: {issue.likely_cause}")

    lines.extend(["", "## Remediation Checklist"])
    for issue in issues:
        lines.append(f"- [{issue.level}] {issue.remediation}")

    highest = max(issue.severity for issue in issues)
    lines.extend(["", "## Priority"])
    if highest >= 5:
        lines.append("Treat this as high priority because at least one critical or repeated severe issue was found.")
    elif highest >= 4:
        lines.append("Review this soon because errors are present.")
    else:
        lines.append("Monitor and address during normal maintenance.")
    return "\n".join(lines)


def analyze_logs(log_text: str) -> str:
    parsed = log_parser(log_text)
    issues = issue_investigator(parsed)
    return fix_recommender(issues)


def load_sample(name: str) -> str:
    return SAMPLES[name].read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze logs with a multi-agent triage workflow.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sample", choices=sorted(SAMPLES))
    source.add_argument("--file", type=Path)
    source.add_argument("--inline")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.sample:
        log_text = load_sample(args.sample)
    elif args.file:
        log_text = args.file.read_text(encoding="utf-8")
    else:
        log_text = args.inline

    print(analyze_logs(log_text))


if __name__ == "__main__":
    main()
