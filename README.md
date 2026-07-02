# Multi-Agent Log Analyzer

Multi-Agent Log Analyzer is a CLI-first Python utility for triaging application logs. It parses warning, error, and critical events, groups repeated issues, infers likely causes, and generates a Markdown remediation report suitable for operational handoff.

## Operational Context

The system supports incident review and service-health investigation where engineers need a quick, repeatable summary of noisy logs. It can run against bundled sample logs, pasted inline logs, or local log files without external services.

## Agent Workflow

- **Log Parser:** extracts warning, error, and critical events from raw log text.
- **Issue Investigator:** groups repeated events and assigns a severity score.
- **Fix Recommender:** maps issue patterns to likely causes and remediation steps.

## Capabilities

- CLI analysis for sample, inline, or file-based logs
- Optional Streamlit interface for interactive review
- Grouping of repeated operational events
- Severity assessment across warning, error, and critical levels
- Root-cause notes for common failure patterns
- Markdown remediation report generation

## Repository Structure

```text
multi-agent-log-analyzer/
|-- app.py
|-- src/
|   |-- __init__.py
|   `-- log_analyzer.py
|-- sample_data/
|   |-- auth.log
|   |-- database.log
|   `-- web.log
|-- screenshots/
|   `-- .gitkeep
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

## Report Output

Generated reports include:

- issue triage table
- severity assessment
- likely root-cause notes
- remediation checklist
- priority recommendation
