from __future__ import annotations

import re
from collections import Counter

from src.schemas import EscalationDecision, InvestigatedIssue, ParsedIssue, PriorityAssessment

LEVEL_SCORE = {"WARNING": 2, "ERROR": 4, "CRITICAL": 5}
ISSUE_PATTERN = re.compile(r"^(?:(?P<timestamp>\S+)\s+)?(?P<level>WARNING|ERROR|CRITICAL)\s+(?P<message>.*)$")
ATTRIBUTE_PATTERN = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>[^\s]+)")


def parse_issue_line(line: str) -> ParsedIssue | None:
    match = ISSUE_PATTERN.search(line)
    if not match:
        return None
    message = match.group("message").strip()
    attributes = {
        match.group("key"): match.group("value")
        for match in ATTRIBUTE_PATTERN.finditer(message)
    }
    return ParsedIssue(
        level=match.group("level"),
        message=message,
        timestamp=match.group("timestamp"),
        attributes=attributes,
        raw_line=line,
    )


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
        group_items = [issue for issue in parsed_issues if issue.level == level and issue.message == message]
        timestamps = [issue.timestamp for issue in group_items if issue.timestamp]
        affected_entities = sorted(
            {
                value
                for issue in group_items
                for key, value in issue.attributes.items()
                if key in {"service", "endpoint", "table", "user", "ip", "source_ip"}
            }
        )
        severity = min(5, LEVEL_SCORE[level] + (1 if count > 1 else 0))
        investigated.append(
            InvestigatedIssue(
                level=level,
                message=message,
                count=count,
                severity=severity,
                first_seen=min(timestamps) if timestamps else None,
                last_seen=max(timestamps) if timestamps else None,
                affected_entities=affected_entities,
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


def decide_escalation(priority: PriorityAssessment, issues: list[InvestigatedIssue]) -> EscalationDecision:
    if priority.priority != "High":
        return EscalationDecision(
            required=False,
            channel="None",
            rationale="No high-priority incident pattern was detected.",
            owner_hint="Service owner review during normal triage.",
        )

    critical_or_repeated = [
        issue
        for issue in issues
        if issue.level == "CRITICAL" or issue.count > 1 or issue.severity >= 5
    ]
    entities = sorted({entity for issue in critical_or_repeated for entity in issue.affected_entities})
    owner_hint = f"Escalate to owner for {', '.join(entities)}." if entities else "Escalate to the on-call service owner."
    return EscalationDecision(
        required=True,
        channel="On-call incident review",
        rationale=priority.rationale,
        owner_hint=owner_hint,
    )
