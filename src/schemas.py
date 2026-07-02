from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field


class ParsedIssue(BaseModel):
    level: str
    message: str
    timestamp: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)
    raw_line: str


class InvestigatedIssue(BaseModel):
    level: str
    message: str
    count: int
    severity: int
    first_seen: str | None = None
    last_seen: str | None = None
    affected_entities: list[str] = Field(default_factory=list)
    likely_cause: str
    remediation: str


class PriorityAssessment(BaseModel):
    highest_severity: int
    priority: str
    rationale: str


class EscalationDecision(BaseModel):
    required: bool
    channel: str
    rationale: str
    owner_hint: str


class TraceEvent(BaseModel):
    node: str
    summary: str


class LogAnalysisState(TypedDict, total=False):
    log_text: str
    parsed_issues: list[ParsedIssue]
    investigated_issues: list[InvestigatedIssue]
    priority: PriorityAssessment
    escalation: EscalationDecision
    report: str
    execution_mode: str
    completed_nodes: list[str]
    trace_events: list[TraceEvent]
    warnings: list[str]
