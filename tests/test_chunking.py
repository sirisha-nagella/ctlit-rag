"""
Hermetic tests for chunking.py — the module that actually builds the live
Chroma store. No network, no data files: everything runs off inline fixtures.

Run:  python -m pytest tests/         (or)  python tests/test_chunking.py
"""

import os
import sys

# make the project root importable whether run via pytest or directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chunking import trial_to_chunks, paper_to_chunks

# ---- fixtures -------------------------------------------------------------

TRIAL = {
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT00000001",
            "briefTitle": "A Study of Drug X in Chronic Hepatitis B",
        },
        "descriptionModule": {"briefSummary": "Evaluating Drug X in chronic HBV."},
        "conditionsModule": {"conditions": ["Hepatitis B", "Chronic HBV"]},
        "eligibilityModule": {"eligibilityCriteria": "Adults 18+ with chronic HBV."},
    }
}

TRIAL_NO_CRITERIA = {
    "protocolSection": {
        "identificationModule": {"nctId": "NCT00000002", "briefTitle": "No-Criteria Trial"},
        "descriptionModule": {"briefSummary": "A summary."},
        "conditionsModule": {"conditions": ["Condition A"]},
        "eligibilityModule": {},  # no eligibilityCriteria
    }
}

PAPER = {"pmid": "12345678", "title": "A Paper on Sofosbuvir", "abstract": "Results were good."}


# ---- trial chunking -------------------------------------------------------

def test_trial_produces_overview_and_eligibility():
    chunks = trial_to_chunks(TRIAL)
    sections = [c["metadata"]["section"] for c in chunks]
    assert sections == ["overview", "eligibility"]
    assert chunks[0]["id"] == "NCT00000001_overview"
    assert chunks[1]["id"] == "NCT00000001_eligibility"


def test_trial_overview_is_self_contained():
    overview = trial_to_chunks(TRIAL)[0]["text"]
    # title, conditions and summary must be stitched into the chunk text
    assert "NCT00000001" in overview
    assert "Chronic Hepatitis B" in overview
    assert "Hepatitis B" in overview
    assert "Drug X" in overview


def test_trial_without_criteria_skips_eligibility():
    chunks = trial_to_chunks(TRIAL_NO_CRITERIA)
    assert [c["metadata"]["section"] for c in chunks] == ["overview"]


# ---- literature chunking --------------------------------------------------

def test_paper_produces_one_chunk():
    chunks = paper_to_chunks(PAPER)
    assert len(chunks) == 1
    assert chunks[0]["id"] == "PMID12345678"
    assert "Sofosbuvir" in chunks[0]["text"]
    assert "Results were good" in chunks[0]["text"]


# ---- the contract app.py / search.py rely on ------------------------------

def test_metadata_contract_holds_for_every_chunk():
    """app.py does meta['source'] and meta.get('nct_id') or meta.get('pmid')."""
    all_chunks = trial_to_chunks(TRIAL) + paper_to_chunks(PAPER)
    for c in all_chunks:
        meta = c["metadata"]
        assert meta["source"] in ("clinical_trial", "literature")
        assert meta.get("nct_id") or meta.get("pmid"), "chunk needs an NCT id or PMID"
        assert "section" in meta
        assert "title" in meta


if __name__ == "__main__":
    # allow plain `python tests/test_chunking.py` without pytest installed
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")
