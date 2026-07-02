from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field


class ParsedIssue(BaseModel):
    level: str
    message: str


class InvestigatedIssue(BaseModel):
    level: str
    message: str
    count: int
    severity: int
    likely_cause: str
    remediation: str


class PriorityAssessment(BaseModel):
    highest_severity: int
    priority: str
    rationale: str


class LogAnalysisState(TypedDict, total=False):
    log_text: str
    parsed_issues: list[ParsedIssue]
    investigated_issues: list[InvestigatedIssue]
    priority: PriorityAssessment
    report: str
    execution_mode: str
    completed_nodes: list[str]
    warnings: list[str]
