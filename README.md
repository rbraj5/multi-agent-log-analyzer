# Multi-Agent Log Analyzer

## Overview
Multi-Agent Log Analyzer is a production-ready local container service for operational log triage. It combines LangGraph orchestration, deterministic tool-style parsing, Pydantic validation, FastAPI backend integration, Docker packaging, and optional LangChain/OpenAI synthesis.

The service remains usable without an API key. Deterministic fallback is the default path; optional LLM synthesis is only used to improve the wording of the remediation report from structured findings.

## Production Use Case
The application supports incident review and service-health investigation where engineers need repeatable analysis of noisy logs before escalating to on-call teams. It parses warning, error, and critical entries, groups repeated issues, assigns severity, routes high-priority incidents through an escalation branch, and produces an operational handoff report.

## Architecture
- FastAPI exposes the workflow as a service API with OpenAPI documentation at `/docs`.
- LangGraph controls the workflow state and conditional escalation route.
- Deterministic Python tools perform parsing, grouping, severity scoring, and remediation mapping.
- Pydantic models validate API payloads and structure workflow responses.
- Docker packages the API as a production-ready local container.
- Trace events, completed nodes, request IDs, and warnings provide lightweight observability.
- LangSmith tracing can be enabled through environment variables when needed.

## LangGraph Workflow
```text
parse_logs -> investigate_issues -> prioritize_findings -> escalate_incident? -> recommend_remediation
```

- `parse_logs`: extracts warning, error, and critical events from raw log text.
- `investigate_issues`: groups repeated events and attaches likely causes and remediation guidance.
- `prioritize_findings`: assigns overall priority based on highest severity.
- `escalate_incident`: conditionally routes high-priority runs through an on-call escalation decision.
- `recommend_remediation`: generates the final Markdown handoff through deterministic fallback or optional LLM synthesis.

## API Usage
Run locally, then open the interactive FastAPI docs:

```powershell
http://localhost:8000/docs
```

Health and metadata:

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/metadata
```

Workflow request:

```powershell
curl -X POST http://localhost:8000/workflow `
  -H "Content-Type: application/json" `
  -d "{\"log_text\":\"2026-06-15T09:01:19 ERROR upstream timeout service=payment-gateway endpoint=/checkout\",\"source_name\":\"checkout-api\"}"
```

The response includes `request_id`, `execution_mode`, `completed_nodes`, `trace_events`, `events`, `issues`, `priority`, `escalation_decision`, `remediation_report`, and `warnings`.

## Docker Run
Build and run the API container locally:

```powershell
docker build -t multi-agent-log-analyzer:local .
docker run --rm -p 8000:8000 --env-file .env.example multi-agent-log-analyzer:local
```

The Docker health check calls `/health`. The container starts the API with:

```powershell
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

## Local Streamlit/CLI Demo
The production API does not replace the original demo paths.

CLI:

```powershell
python -m src.log_analyzer --sample web
python -m src.log_analyzer --sample database
python -m src.log_analyzer --sample auth
python -m src.log_analyzer --inline "2026-06-15 ERROR payment timeout"
```

Streamlit:

```powershell
streamlit run app.py
```

## Configuration
Use `.env.example` as the configuration template:

```text
APP_ENV=local
APP_VERSION=0.1.0
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LOG_LEVEL=INFO
```

No OpenAI or LangSmith configuration is required for deterministic operation. Do not commit secrets or cloud credentials.

## Testing
Run local checks:

```powershell
python -m compileall .
python -m unittest discover -s tests
docker build -t multi-agent-log-analyzer:local .
```

The test suite includes workflow tests, FastAPI endpoint tests, and README contract tests that enforce the required documentation structure.

## Azure Container Apps Deployment Path
This repo is Azure Container Apps ready, but no cloud deployment is required for the local demo.

Example deployment path:

```powershell
az group create --name rg-agentic-ai-demo --location uksouth
az containerapp env create --name cae-agentic-ai-demo --resource-group rg-agentic-ai-demo --location uksouth
az containerapp create `
  --name log-analyzer-api `
  --resource-group rg-agentic-ai-demo `
  --environment cae-agentic-ai-demo `
  --image <registry>/multi-agent-log-analyzer:latest `
  --target-port 8000 `
  --ingress external `
  --env-vars APP_ENV=azure APP_VERSION=0.1.0 LOG_LEVEL=INFO
```

Configure secrets such as `OPENAI_API_KEY` through Azure Container Apps secret management, not in source control.

## Production Readiness Notes
- FastAPI backend available.
- Docker image buildable.
- Health and readiness endpoints available.
- Pydantic request/response validation.
- Deterministic fallback without API key.
- Optional LangChain/OpenAI synthesis.
- Trace events returned in API responses.
- CI validates compile/tests/Docker build.
- Azure Container Apps deployment path documented.

## Limitations and Next Steps
- Authentication and rate limiting are not implemented.
- Logs are processed per request and are not persisted.
- Azure deployment commands are documented but not executed here.
- Future extensions would add durable LangGraph checkpointing, LangSmith tracing dashboards, structured JSON log ingestion, service ownership metadata, and incident correlation across services.
