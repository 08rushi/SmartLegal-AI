# evaluation_datasets/

This directory stores **human-verified ground-truth annotation files** for Phase 7 accuracy evaluation.

## ⚠️ PII Warning

Real legal documents (rental agreements, employment contracts, loan documents, NDAs, etc.) **MUST be PII-scrubbed** before being placed in this directory. Remove all personally identifiable information:
- Names (parties, landlords, tenants, employees)
- Addresses
- Aadhar/PAN/passport numbers
- Phone numbers / email addresses
- Bank account details

If this directory contains real legal documents, **add it to `.gitignore`** to prevent committing sensitive content.

## File Format

Each ground-truth document is stored as a JSON file named:
```
{document_id}_gt.json
```

The corresponding source PDF must be in the same directory with the filename matching `GroundTruthDocument.filename`.

## JSON Schema (schema_version: 7.1)

```json
{
  "corpus_id": "smartlegal_v1",
  "corpus_version": "1.0.0",
  "document_id": "rental_001_devanagari",
  "filename": "rental_001_scrubbed.pdf",
  "source_hash": "<sha256-hex-of-pdf-bytes>",
  "document_type": "rental_agreement",
  "expected_document_class": "scanned_pdf",
  "language": "hi",
  "indic_scripts": ["Devanagari"],
  "page_count": 3,
  "dataset_version": "1.0.0",
  "schema_version": "7.1",
  "created_at": "2026-09-01T10:00:00Z",
  "notes": "",
  "pages": [
    {
      "page_num": 1,
      "reference_text": "यह किराया समझौता...",
      "script": "Hindi / Marathi (Devanagari)",
      "expected_page_type": "scanned",
      "expected_is_unclear": false,
      "annotation_version": "1.0",
      "annotation": {
        "annotator_id": "annotator_01",
        "annotation_date": "2026-09-01",
        "review_state": "approved",
        "reviewer_id": "reviewer_01",
        "reviewed_at": "2026-09-02",
        "notes": ""
      }
    }
  ]
}
```

## `review_state` Lifecycle

| State | Contributes to Metrics? | Count As |
|---|---|---|
| `approved` | ✅ Yes | evaluated |
| `draft` | ❌ No | skipped |
| `review_pending` | ❌ No | skipped |
| `rejected` | ❌ No | skipped |

Only `approved` pages are included in CER/WER computations.

## Computing `source_hash`

```python
import hashlib
with open("document.pdf", "rb") as f:
    source_hash = hashlib.sha256(f.read()).hexdigest()
```

## Legal Accuracy Disclaimer

CER/WER metrics measure **transcription fidelity only**. They do **NOT** measure:
- Legal accuracy
- Semantic correctness
- Contractual correctness
- Legal validity
