# Multi-Agent Log Analyzer

A CLI-first Python project that reviews application logs through a small multi-agent workflow.

Agents:

- Log Parser
- Issue Investigator
- Fix Recommender

The app includes sample logs and can run without paid APIs.

## Features

- Analyze bundled sample logs
- Analyze pasted inline logs
- Analyze a local `.log` or `.txt` file
- Extract warnings, errors, and critical events
- Group repeated issues
- Generate a Markdown remediation report
- Optional Streamlit interface

## Project Structure

```text
multi-agent-log-analyzer/
├── app.py
├── src/
│   ├── __init__.py
│   └── log_analyzer.py
├── sample_data/
│   ├── auth.log
│   ├── database.log
│   └── web.log
├── screenshots/
│   └── .gitkeep
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Setup

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

## Output

The analyzer prints a Markdown report with:

- Issue summary
- Severity assessment
- Likely root cause
- Suggested remediation checklist

