"""Regression tests for reported document-analysis failures."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.groq_service import _normalize_clause_payload
from services.chunking_service import classify_chunk_error


class TestClauseResponseNormalization(unittest.TestCase):
    def test_plain_array_is_preserved(self):
        clauses = [{"title": "Payment", "original_text": "Rent is due monthly."}]
        self.assertEqual(_normalize_clause_payload(clauses), clauses)

    def test_wrapped_clauses_object_is_unwrapped(self):
        clauses = [{"title": "Payment", "original_text": "Rent is due monthly."}]
        self.assertEqual(_normalize_clause_payload({"clauses": clauses}), clauses)

    def test_nested_data_wrapper_is_unwrapped(self):
        clauses = [{"title": "Termination", "original_text": "Thirty days notice."}]
        self.assertEqual(_normalize_clause_payload({"data": {"clauses": clauses}}), clauses)

    def test_single_clause_object_is_wrapped(self):
        clause = {"title": "Indemnity", "original_text": "The party indemnifies..."}
        self.assertEqual(_normalize_clause_payload(clause), [clause])

    def test_unrelated_object_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, "without a clause array"):
            _normalize_clause_payload({"message": "model refused"})

    def test_empty_array_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, "no usable clauses"):
            _normalize_clause_payload([])


class TestMalformedShapeRetryClassification(unittest.TestCase):
    def test_wrapped_response_shape_is_retryable(self):
        self.assertEqual(classify_chunk_error(ValueError("AI returned a JSON object without a clause array")), "malformed_response")


if __name__ == "__main__":
    unittest.main()
