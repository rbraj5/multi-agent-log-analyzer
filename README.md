# Multi-Agent Log Analyzer

Multi-Agent Log Analyzer is a CLI-first Python utility for triaging application logs. The application uses LangGraph to orchestrate parsing, investigation, prioritization, and remediation reporting, with optional LangChain/OpenAI synthesis for operational handoff notes.

## Operational Context

The system supports incident review and service-health investigation where engineers need a quick, repeatable summary of noisy logs. Parsing, grouping, severity scoring, and remediation mapping are deterministic so operational facts remain reproducible.

## LangGraph Workflow

```text
parse_logs -> investigate_issues -> prioritize_findings -> escalate_incident? -> recommend_remediation
```

- **parse_logs:** extracts warning, error, and critical events from raw log text.
- **investigate_issues:** groups repeated events and attaches likely causes and remediation guidance.
- **prioritize_findings:** assigns overall priority based on highest severity.
- **escalate_incident:** conditionally routes high-priority runs through an on-call escalation decision.
- **recommend_remediation:** generates the final Markdown handoff through deterministic fallback or optional LLM synthesis.

## Execution Modes

- **Deterministic fallback:** runs without API keys and generates reports from structured issue findings.
- **LLM-assisted synthesis:** uses `langchain-openai` when `OPENAI_API_KEY` is configured. The LLM receives structured incident summaries only.

## Capabilities

- CLI analysis for sample, inline, or file-based logs
- Optional Streamlit interface for interactive review
- LangGraph node execution trace in the UI
- Grouping of repeated operational events
- Timestamp, key-value attribute, and affected-entity extraction
- Severity assessment across warning, error, and critical levels
- Conditional escalation branch for high-priority incidents
- Structured graph trace events for node-level observability
- Markdown remediation report generation

## Productionization Notes

The graph now includes conditional routing rather than a purely linear flow. High-priority incidents take an escalation branch before remediation, while normal warning-only logs skip escalation. This mirrors a common production incident workflow where severe findings require an on-call review path and lower-priority findings stay in routine triage.

Future production extensions would include durable LangGraph checkpointing, LangSmith tracing, deployment configuration, structured JSON log ingestion, service ownership metadata, and incident timeline correlation across multiple services.

## Repository Structure

```text
multi-agent-log-analyzer/
|-- app.py
|-- src/
|   |-- __init__.py
|   |-- graph.py
|   |-- log_analyzer.py
|   |-- schemas.py
|   `-- tools.py
|-- sample_data/
|   |-- auth.log
|   |-- database.log
|   `-- web.log
|-- .env.example
|-- .gitignore
|-- LICENSE
|-- README.md
`-- requirements.txt
```

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## CLI Usage

```powershell
python -m src.log_analyzer --sample web
python -m src.log_analyzer --sample database
python -m src.log_analyzer --sample auth
python -m src.log_analyzer --file .\sample_data\web.log
python -m src.log_analyzer --inline "2026-06-15 ERROR payment timeout"
```

## Streamlit Usage

```powershell
streamlit run app.py
```
