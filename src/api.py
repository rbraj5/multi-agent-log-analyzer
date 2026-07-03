from __future__ import annotations

import logging
import os
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.graph import run_log_analysis_workflow

PROJECT_NAME = "Multi-Agent Log Analyzer"
WORKFLOW_NODES = [
    "parse_logs",
    "investigate_issues",
    "prioritize_findings",
    "escalate_incident",
    "recommend_remediation",
]

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("log_analyzer_api")

app = FastAPI(
    title=PROJECT_NAME,
    version=os.getenv("APP_VERSION", "0.1.0"),
    description="Production-ready FastAPI wrapper for the LangGraph log triage workflow.",
)


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    environment: str


class MetadataResponse(BaseModel):
    service: str
    workflow_nodes: list[str]
    execution_modes: list[str]
    llm_configured: bool


class LogWorkflowRequest(BaseModel):
    log_text: str = Field(..., min_length=1)
    source_name: str | None = None


class LogWorkflowResponse(BaseModel):
    request_id: str
    source_name: str | None
    execution_mode: str
    completed_nodes: list[str]
    trace_events: list[dict]
    warnings: list[str]
    events: list[dict]
    issues: list[dict]
    priority: dict
    escalation_decision: dict | None
    remediation_report: str


@app.get("/health", response_model=HealthResponse, summary="Container health check")
def health() -> HealthResponse:
    return HealthResponse(
        service=PROJECT_NAME,
        version=os.getenv("APP_VERSION", "0.1.0"),
        status="healthy",
        environment=os.getenv("APP_ENV", "local"),
    )


@app.get("/ready", response_model=HealthResponse, summary="Runtime readiness check")
def ready() -> HealthResponse:
    # Import and graph entrypoint are already loaded; this endpoint confirms API readiness for probes.
    return HealthResponse(
        service=PROJECT_NAME,
        version=os.getenv("APP_VERSION", "0.1.0"),
        status="ready",
        environment=os.getenv("APP_ENV", "local"),
    )


@app.get("/metadata", response_model=MetadataResponse, summary="Workflow metadata")
def metadata() -> MetadataResponse:
    return MetadataResponse(
        service=PROJECT_NAME,
        workflow_nodes=WORKFLOW_NODES,
        execution_modes=["Deterministic fallback", "LLM-assisted synthesis"],
        llm_configured=bool(os.getenv("OPENAI_API_KEY")),
    )


@app.post("/workflow", response_model=LogWorkflowResponse, summary="Run the LangGraph log analysis workflow")
def workflow(payload: LogWorkflowRequest) -> LogWorkflowResponse:
    request_id = str(uuid4())
    logger.info("running log workflow request_id=%s source=%s", request_id, payload.source_name or "inline")
    state = run_log_analysis_workflow(payload.log_text)
    return LogWorkflowResponse(
        request_id=request_id,
        source_name=payload.source_name,
        execution_mode=state["execution_mode"],
        completed_nodes=state["completed_nodes"],
        trace_events=[event.model_dump() for event in state.get("trace_events", [])],
        warnings=state.get("warnings", []),
        events=[event.model_dump() for event in state.get("parsed_issues", [])],
        issues=[issue.model_dump() for issue in state.get("investigated_issues", [])],
        priority=state["priority"].model_dump(),
        escalation_decision=state.get("escalation").model_dump() if state.get("escalation") else None,
        remediation_report=state["report"],
    )
