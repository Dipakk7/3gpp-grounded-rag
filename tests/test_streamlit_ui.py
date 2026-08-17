"""
Unit tests for Streamlit Demo UI Helper and Integration Functions (Phase 10).
"""

import unittest
from unittest.mock import patch, MagicMock
from streamlit_app import check_backend_health, query_rag_api


class TestStreamlitUI(unittest.TestCase):
    """Test suite for Streamlit UI helper logic."""

    @patch("streamlit_app.requests.get")
    def test_health_check_online(self, mock_get):
        """Test health check parsing when API is online."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "ok",
            "service": "mavenir-3gpp-rag",
            "details": {"vector_store_chunk_count": 6737},
        }
        mock_get.return_value = mock_resp

        res = check_backend_health()
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["details"]["vector_store_chunk_count"], 6737)

    @patch("streamlit_app.requests.get")
    def test_health_check_offline(self, mock_get):
        """Test health check returns None when connection fails."""
        mock_get.side_effect = Exception("Connection refused")
        res = check_backend_health()
        self.assertIsNone(res)

    @patch("streamlit_app.requests.post")
    def test_query_rag_api_answered(self, mock_post):
        """Test successful question answering response handling."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "answered",
            "answer": "The NG-U interface connects NG-RAN and UPF.",
            "citations": [
                {
                    "specification": "TS 38.300",
                    "clause_number": "4.3.1.1",
                    "clause_title": "NG User Plane",
                }
            ],
            "evidence": [
                {
                    "evidence_id": "E1",
                    "chunk_id": "chunk_123",
                    "specification": "TS 38.300",
                    "clause_number": "4.3.1.1",
                    "clause_title": "NG User Plane",
                }
            ],
            "reason": None,
            "latency_breakdown": {"retrieval_ms": 10.0, "generation_ms": 200.0},
        }
        mock_post.return_value = mock_resp

        res = query_rag_api("What is NG-U?")
        self.assertTrue(res["success"])
        data = res["data"]
        self.assertEqual(data["status"], "answered")
        self.assertEqual(len(data["citations"]), 1)
        self.assertEqual(data["citations"][0]["specification"], "TS 38.300")

    @patch("streamlit_app.requests.post")
    def test_query_rag_api_abstained(self, mock_post):
        """Test safe abstention response handling."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "abstain",
            "answer": None,
            "citations": [],
            "evidence": [],
            "reason": "The requested information could not be supported.",
            "latency_breakdown": None,
        }
        mock_post.return_value = mock_resp

        res = query_rag_api("What is 7G?")
        self.assertTrue(res["success"])
        data = res["data"]
        self.assertEqual(data["status"], "abstain")
        self.assertIsNone(data["answer"])
        self.assertEqual(data["reason"], "The requested information could not be supported.")

    @patch("streamlit_app.requests.post")
    def test_query_rag_api_validation_error(self, mock_post):
        """Test 422 validation error handling."""
        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.json.return_value = {
            "detail": "question cannot be empty or whitespace-only",
            "error_code": "VALIDATION_ERROR",
        }
        mock_post.return_value = mock_resp

        res = query_rag_api("   ")
        self.assertFalse(res["success"])
        self.assertIn("Validation Error", res["error"])
        self.assertNotIn("Traceback", res["error"])

    @patch("streamlit_app.requests.post")
    def test_query_rag_api_connection_error(self, mock_post):
        """Test graceful connection error handling without traceback leakage."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        res = query_rag_api("What is AMF?")
        self.assertFalse(res["success"])
        self.assertIn("Connection Error", res["error"])
        self.assertNotIn("Traceback", res["error"])


if __name__ == "__main__":
    unittest.main()
