from __future__ import annotations

import os

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from src.schemas import LogAnalysisState, TraceEvent
from src.tools import decide_escalation, investigate_issues, parse_logs, prioritize_findings


def _completed(state: LogAnalysisState, node: str) -> list[str]:
    return [*state.get("completed_nodes", []), node]


def _trace(state: LogAnalysisState, node: str, summary: str) -> list[TraceEvent]:
    return [*state.get("trace_events", []), TraceEvent(node=node, summary=summary)]


def _parse_node(state: LogAnalysisState) -> LogAnalysisState:
    parsed = parse_logs(state["log_text"])
    return {
        "parsed_issues": parsed,
        "completed_nodes": _completed(state, "parse_logs"),
        "trace_events": _trace(state, "parse_logs", f"Extracted {len(parsed)} warning/error/critical events."),
    }


def _investigate_node(state: LogAnalysisState) -> LogAnalysisState:
    investigated = investigate_issues(state["parsed_issues"])
    return {
        "investigated_issues": investigated,
        "completed_nodes": _completed(state, "investigate_issues"),
        "trace_events": _trace(state, "investigate_issues", f"Grouped events into {len(investigated)} issue pattern(s)."),
    }


def _prioritize_node(state: LogAnalysisState) -> LogAnalysisState:
    priority = prioritize_findings(state["investigated_issues"])
    return {
        "priority": priority,
        "completed_nodes": _completed(state, "prioritize_findings"),
        "trace_events": _trace(state, "prioritize_findings", f"Assigned {priority.priority} priority."),
    }


def _route_after_priority(state: LogAnalysisState) -> str:
    if state["priority"].priority == "High":
        return "escalate_incident"
    return "recommend_remediation"


def _escalation_node(state: LogAnalysisState) -> LogAnalysisState:
    escalation = decide_escalation(state["priority"], state["investigated_issues"])
    return {
        "escalation": escalation,
        "completed_nodes": _completed(state, "escalate_incident"),
        "trace_events": _trace(state, "escalate_incident", escalation.rationale),
    }


def _deterministic_report(state: LogAnalysisState) -> str:
    issues = state["investigated_issues"]
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

    lines.extend(["", "## Incident Timeline"])
    for issue in issues:
        window = "unknown"
        if issue.first_seen and issue.last_seen:
            window = issue.first_seen if issue.first_seen == issue.last_seen else f"{issue.first_seen} to {issue.last_seen}"
        entities = ", ".join(issue.affected_entities) or "not identified"
        lines.append(f"- **{issue.message}**: {window}; affected entities: {entities}")

    lines.extend(["", "## Root Cause Notes"])
    for issue in issues:
        lines.append(f"- **{issue.message}**: {issue.likely_cause}")

    lines.extend(["", "## Remediation Checklist"])
    for issue in issues:
        lines.append(f"- [{issue.level}] {issue.remediation}")

    priority = state["priority"]
    lines.extend(["", "## Priority", f"**{priority.priority}:** {priority.rationale}"])
    escalation = state.get("escalation")
    if escalation:
        lines.extend(
            [
                "",
                "## Escalation",
                f"- Required: {'yes' if escalation.required else 'no'}",
                f"- Channel: {escalation.channel}",
                f"- Owner hint: {escalation.owner_hint}",
            ]
        )
    return "\n".join(lines)


def _llm_report(state: LogAnalysisState) -> tuple[str, list[str]]:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        return _deterministic_report(state), []

    try:
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
        response = model.invoke(
            "Create a concise operational log-analysis handoff. "
            "Use only the structured findings below. Do not invent incidents.\n\n"
            f"Issues: {[issue.model_dump() for issue in state['investigated_issues']]}\n"
            f"Priority: {state['priority'].model_dump()}\n"
            f"Escalation: {state.get('escalation').model_dump() if state.get('escalation') else None}\n"
        )
        return str(response.content), []
    except Exception as exc:  # pragma: no cover
        return _deterministic_report(state), [f"LLM synthesis failed; deterministic report used. Reason: {exc}"]


def _remediation_node(state: LogAnalysisState) -> LogAnalysisState:
    report, warnings = _llm_report(state)
    execution_mode = "LLM-assisted synthesis" if os.getenv("OPENAI_API_KEY") and not warnings else "Deterministic fallback"
    return {
        "report": report,
        "warnings": [*state.get("warnings", []), *warnings],
        "execution_mode": execution_mode,
        "completed_nodes": _completed(state, "recommend_remediation"),
        "trace_events": _trace(state, "recommend_remediation", f"Generated report in {execution_mode} mode."),
    }


def build_graph():
    graph = StateGraph(LogAnalysisState)
    graph.add_node("parse_logs", _parse_node)
    graph.add_node("investigate_issues", _investigate_node)
    graph.add_node("prioritize_findings", _prioritize_node)
    graph.add_node("escalate_incident", _escalation_node)
    graph.add_node("recommend_remediation", _remediation_node)
    graph.add_edge(START, "parse_logs")
    graph.add_edge("parse_logs", "investigate_issues")
    graph.add_edge("investigate_issues", "prioritize_findings")
    graph.add_conditional_edges(
        "prioritize_findings",
        _route_after_priority,
        {
            "escalate_incident": "escalate_incident",
            "recommend_remediation": "recommend_remediation",
        },
    )
    graph.add_edge("escalate_incident", "recommend_remediation")
    graph.add_edge("recommend_remediation", END)
    return graph.compile()


def run_log_analysis_workflow(log_text: str) -> LogAnalysisState:
    return build_graph().invoke(
        {
            "log_text": log_text,
            "completed_nodes": [],
            "trace_events": [],
            "warnings": [],
            "execution_mode": "Deterministic fallback",
        }
    )
