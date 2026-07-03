from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

from src.api import app


class LogAnalyzerApiTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        self.client = TestClient(app)

    def test_health_ready_and_metadata(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/ready").status_code, 200)
        metadata = self.client.get("/metadata").json()
        self.assertIn("parse_logs", metadata["workflow_nodes"])
        self.assertIn("Deterministic fallback", metadata["execution_modes"])

    def test_workflow_returns_structured_response(self) -> None:
        response = self.client.post(
            "/workflow",
            json={"log_text": "2026-06-15T09:01:19 ERROR upstream timeout service=payment-gateway", "source_name": "smoke"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["execution_mode"], "Deterministic fallback")
        self.assertIn("request_id", payload)
        self.assertIn("parse_logs", payload["completed_nodes"])
        self.assertGreaterEqual(len(payload["events"]), 1)
        self.assertIn("priority", payload)

    def test_invalid_payload_is_rejected(self) -> None:
        response = self.client.post("/workflow", json={"log_text": ""})

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
