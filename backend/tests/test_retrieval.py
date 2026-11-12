import unittest

from services.retrieval import select_relevant_text


def _doc(pages: int = 40) -> str:
    out = []
    for p in range(1, pages + 1):
        body = f"Page {p} general boilerplate text about maintenance and society charges. " * 18
        if p == 31:
            body += " The arbitration seat shall be Pune and the penalty for early termination is three months rent. "
        out.append(f"[Page {p}]\n{body}")
    return "\n\n".join(out)


class TestSelectRelevantText(unittest.TestCase):
    def test_short_documents_are_unchanged(self):
        self.assertEqual(select_relevant_text("short text", "anything"), "short text")

    def test_pulls_in_a_late_page_that_matches_the_question(self):
        doc = _doc()
        self.assertNotIn("arbitration seat", doc[:12000])   # the old behaviour would miss it
        picked = select_relevant_text(doc, "Where is the arbitration seat?")
        self.assertIn("arbitration seat", picked)
        self.assertIn("[Page 1]", picked)                   # opening is always kept
        self.assertLessEqual(len(picked), 12300)

    def test_generic_question_falls_back_to_document_start(self):
        picked = select_relevant_text(_doc(), "summarize this")
        self.assertTrue(picked.startswith("[Page 1]"))
        self.assertIn("[Page 2]", picked)

    def test_works_without_page_markers_and_with_hindi_terms(self):
        paras = [("साधारण अटी और शर्तें " * 40) for _ in range(30)]
        paras[22] = "किराया वाढ पाच टक्के दरवर्षी लागू होईल " * 10
        doc = "\n\n".join(paras)
        picked = select_relevant_text(doc, "किराया वाढ किती आहे")
        self.assertIn("किराया वाढ पाच टक्के", picked)


if __name__ == "__main__":
    unittest.main()
