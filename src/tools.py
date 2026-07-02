from __future__ import annotations

import re
from collections import Counter

from src.schemas import InvestigatedIssue, ParsedIssue, PriorityAssessment

LEVEL_SCORE = {"WARNING": 2, "ERROR": 4, "CRITICAL": 5}


def parse_issue_line(line: str) -> ParsedIssue | None:
    match = re.search(r"\b(WARNING|ERROR|CRITICAL)\b\s+(.*)", line)
    if not match:
        return None
    return ParsedIssue(level=match.group(1), message=match.group(2).strip())


def parse_logs(log_text: str) -> list[ParsedIssue]:
    issues: list[ParsedIssue] = []
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


def investigate_issues(parsed_issues: list[ParsedIssue]) -> list[InvestigatedIssue]:
    grouped = Counter((issue.level, issue.message) for issue in parsed_issues)
    investigated: list[InvestigatedIssue] = []
    for (level, message), count in grouped.most_common():
        severity = min(5, LEVEL_SCORE[level] + (1 if count > 1 else 0))
        investigated.append(
            InvestigatedIssue(
                level=level,
                message=message,
                count=count,
                severity=severity,
                likely_cause=infer_cause(message),
                remediation=recommend_fix(message),
            )
        )
    return investigated


def prioritize_findings(issues: list[InvestigatedIssue]) -> PriorityAssessment:
    if not issues:
        return PriorityAssessment(
            highest_severity=0,
            priority="No action required",
            rationale="No warning, error, or critical entries were found.",
        )

    highest = max(issue.severity for issue in issues)
    if highest >= 5:
        return PriorityAssessment(
            highest_severity=highest,
            priority="High",
            rationale="At least one critical or repeated severe issue was found.",
        )
    if highest >= 4:
        return PriorityAssessment(
            highest_severity=highest,
            priority="Medium",
            rationale="Errors are present and should be reviewed soon.",
        )
    return PriorityAssessment(
        highest_severity=highest,
        priority="Normal",
        rationale="Warnings are present and can be handled during normal maintenance.",
    )
