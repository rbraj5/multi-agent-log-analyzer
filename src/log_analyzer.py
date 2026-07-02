from __future__ import annotations

import argparse
from pathlib import Path

from src.graph import run_log_analysis_workflow


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = {
    "web": ROOT / "sample_data/web.log",
    "database": ROOT / "sample_data/database.log",
    "auth": ROOT / "sample_data/auth.log",
}


def load_sample(name: str) -> str:
    return SAMPLES[name].read_text(encoding="utf-8")


def analyze_logs(log_text: str) -> str:
    return run_log_analysis_workflow(log_text)["report"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze logs with a LangGraph triage workflow.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sample", choices=sorted(SAMPLES))
    source.add_argument("--file", type=Path)
    source.add_argument("--inline")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.sample:
        log_text = load_sample(args.sample)
    elif args.file:
        log_text = args.file.read_text(encoding="utf-8")
    else:
        log_text = args.inline

    print(analyze_logs(log_text))


if __name__ == "__main__":
    main()
