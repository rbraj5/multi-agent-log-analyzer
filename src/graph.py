from __future__ import annotations

import os

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from src.schemas import LogAnalysisState
from src.tools import investigate_issues, parse_logs, prioritize_findings


def _completed(state: LogAnalysisState, node: str) -> list[str]:
    return [*state.get("completed_nodes", []), node]


def _parse_node(state: LogAnalysisState) -> LogAnalysisState:
    return {
        "parsed_issues": parse_logs(state["log_text"]),
        "completed_nodes": _completed(state, "parse_logs"),
    }


def _investigate_node(state: LogAnalysisState) -> LogAnalysisState:
    return {
        "investigated_issues": investigate_issues(state["parsed_issues"]),
        "completed_nodes": _completed(state, "investigate_issues"),
    }


def _prioritize_node(state: LogAnalysisState) -> LogAnalysisState:
    return {
        "priority": prioritize_findings(state["investigated_issues"]),
        "completed_nodes": _completed(state, "prioritize_findings"),
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

    lines.extend(["", "## Root Cause Notes"])
    for issue in issues:
        lines.append(f"- **{issue.message}**: {issue.likely_cause}")

    lines.extend(["", "## Remediation Checklist"])
    for issue in issues:
        lines.append(f"- [{issue.level}] {issue.remediation}")

    priority = state["priority"]
    lines.extend(["", "## Priority", f"**{priority.priority}:** {priority.rationale}"])
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
    }


def build_graph():
    graph = StateGraph(LogAnalysisState)
    graph.add_node("parse_logs", _parse_node)
    graph.add_node("investigate_issues", _investigate_node)
    graph.add_node("prioritize_findings", _prioritize_node)
    graph.add_node("recommend_remediation", _remediation_node)
    graph.add_edge(START, "parse_logs")
    graph.add_edge("parse_logs", "investigate_issues")
    graph.add_edge("investigate_issues", "prioritize_findings")
    graph.add_edge("prioritize_findings", "recommend_remediation")
    graph.add_edge("recommend_remediation", END)
    return graph.compile()


def run_log_analysis_workflow(log_text: str) -> LogAnalysisState:
    return build_graph().invoke(
        {
            "log_text": log_text,
            "completed_nodes": [],
            "warnings": [],
            "execution_mode": "Deterministic fallback",
        }
    )
