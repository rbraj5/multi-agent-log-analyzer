from __future__ import annotations

import os
import unittest

from src.graph import run_log_analysis_workflow
from src.log_analyzer import load_sample


class LogAnalysisWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)

    def test_web_sample_runs_in_deterministic_mode(self) -> None:
        state = run_log_analysis_workflow(load_sample("web"))

        self.assertEqual(state["execution_mode"], "Deterministic fallback")
        self.assertEqual(
            state["completed_nodes"],
            ["parse_logs", "investigate_issues", "prioritize_findings", "recommend_remediation"],
        )
        self.assertEqual(state["priority"].priority, "High")
        self.assertIn("Log Analysis Report", state["report"])


if __name__ == "__main__":
    unittest.main()
