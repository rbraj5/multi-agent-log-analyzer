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
            ["parse_logs", "investigate_issues", "prioritize_findings", "escalate_incident", "recommend_remediation"],
        )
        self.assertEqual(state["priority"].priority, "High")
        self.assertTrue(state["escalation"].required)
        self.assertIn("Log Analysis Report", state["report"])

    def test_warning_only_log_skips_escalation_branch(self) -> None:
        state = run_log_analysis_workflow("2026-06-15T09:01:14 WARNING request latency high endpoint=/checkout ms=1850")

        self.assertEqual(
            state["completed_nodes"],
            ["parse_logs", "investigate_issues", "prioritize_findings", "recommend_remediation"],
        )
        self.assertNotIn("escalation", state)
        self.assertEqual(state["priority"].priority, "Normal")

    def test_parser_extracts_timestamp_and_attributes(self) -> None:
        state = run_log_analysis_workflow("2026-06-15T09:01:19 ERROR upstream timeout service=payment-gateway endpoint=/checkout")
        issue = state["parsed_issues"][0]

        self.assertEqual(issue.timestamp, "2026-06-15T09:01:19")
        self.assertEqual(issue.attributes["service"], "payment-gateway")
        self.assertEqual(issue.attributes["endpoint"], "/checkout")


if __name__ == "__main__":
    unittest.main()
