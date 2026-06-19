

"""
Turn one trial record into a small list of self-contained text chunks.
Each chunk = {id, text, metadata}. No embedding yet - just clean text."""

def trial_to_chunks(study):
    ps = study["protocolSection"]
    ident = ps["identificationModule"]
    desc = ps.get("descriptionModule", {})
    cond = ps.get("conditionsModule", {})
    elig = ps.get("eligibilityModule", {})

    nct_id = ident["nctId"]
    title = ident["briefTitle"]
    conditions = ", ".join(cond.get("conditions", [])) or "not specified"
    summary = desc.get("briefSummary", "").strip()
    criteria = elig.get("eligibilityCriteria", "").strip()

    chunks = []

    # Chunk 1 - overview. Title is stitched in so the chunk stands alone.
    
    overview = (
        f"Clinical trial {nct_id}: {title}. "
        f"Conditions studied: {conditions}. "
        f"Summary: {summary}"
    )
    chunks.append({
        "id": f"{nct_id}_overview",
        "text": overview,
        "metadata": {"source": "clinical_trial", "nct_id": nct_id, "title": title, "section": "overview"}
    })

    # Chunk 2 - eligibility. Only if the trial actually lists criteria.

    if criteria:
        eligibility = (
            f"Eligibility criteria for trial {nct_id} ({title}): {criteria}"
        )
        chunks.append({
            "id": f"{nct_id}_eligibility",
            "text": eligibility,
            "metadata": {"source": "clinical_trial", "nct_id": nct_id, "title": title, "section": "eligibility"},
        })

    return chunks

# this is literature paper chunking

def paper_to_chunks(paper):
    """A paper is already compact -> one self-contained chunk."""
    pmid = paper["pmid"]
    title = paper["title"]
    abstract = paper["abstract"]

    text = f"Research paper (PMID {pmid}): {title}. Abstract: {abstract}"

    return [{
        "id": f"PMID{pmid}",
        "text": text,
        "metadata": {
            "source": "literature",      # <- the tag that coexists with trials
            "pmid": pmid,
            "title": title,
            "section": "abstract",
        },

    }]


# self-test: chunk one saved trial and print the pieces

if __name__=="__main__":
    import json
    from pathlib import Path

    study = json.loads(Path("data/trials/NCT01590654.json").read_text())
    chunks = trial_to_chunks(study)

    print(f"Produced {len(chunks)} chunks.\n")
    for c in chunks:
        print("ID:    ", c["id"])
        print("SECTION:", c["metadata"]["section"])
        print("TEXT:   ", c["text"][:200], "...\n")

