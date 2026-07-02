
"""
Turn a ClinicalTrials.gov v2 trial JSON into retrieval chunks.
Each chunk carries a header (NCT ID + title) so a retrieved fragment
stays self-contextualizing, plus metadata for filtering and citation.
"""

from sentence_transformers import SentenceTransformer

tok = SentenceTransformer("all-MiniLM-L6-v2").tokenizer

def _safe(d, *keys, default=""):
    """Walk nested dict keys safely; return default if any level is missing."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
        if d is None:
            return default
    return d


def extract_chunks(trial: dict, source_key: str = "") -> list[dict]:
    protocol = trial.get("protocolSection", {})

    ident = protocol.get("identificationModule", {})
    nct_id = ident.get("nctId", "UNKNOWN")
    title = ident.get("officialTitle") or ident.get("briefTitle") or "Untitled trial"

    # shared metadata - identical on every chunk of this trial
    conditions = protocol.get("conditionsModule", {}).get("conditions", [])
    phases = protocol.get("designModule", {}).get("phases", [])
    base_meta = {
        "nct_id": nct_id,
        "title": title,
        "conditions": conditions,
        "phases": phases,
        "status": _safe(protocol, "statusModule", "overallStatus"),
        "sponsor": _safe(protocol, "sponsorCollaboratorsModule", "leadSponsor", "name"),
        "source_key": source_key,
    }

    # the header welded onto every chunk so fragments stay grounded
    header = f"[Trial {nct_id} - {title}]"
    chunks = []

    def add(section: str, body: str):
        body = (body or "").strip()
        if not body:
            return # skip empty sections rather than embedding blanks
        chunks.append({
            "id": f"{nct_id}::{section}",
            "text": f"{header}\n{section.capitalize()}:\n{body}",
            "metadata": {**base_meta, "section": section},
        })

    # 1. Summary (brief + detailed description, same kind of content)
    desc = protocol.get("descriptionModule", {})
    summary = "\n\n".join(p for p in [desc.get("briefSummary"),
                                      desc.get("detailedDescription")] if p)
    add("summary", summary)

    # 2. Conditions
    add("conditions", ", ".join(conditions))

    # 3. Eligibility (structured age/sex bits + the free-text criteria)
    elig = protocol.get("eligibilityModule", {})
    structured = []
    if elig.get("sex"):          structured.append(f"Sex: {elig['sex']}")
    if elig.get("minimumAge"):   structured.append(f"Min age: {elig['minimumAge']}")
    if elig.get("maximumAge"):   structured.append(f"Max age: {elig['maximumAge']}")
    if elig.get("healthyVolunteers") is not None:
        structured.append(f"Healthy volunteers: {elig['healthyVolunteers']}")
    elig_full = "\n".join(filter(None, [" | ".join(structured),
                                        elig.get("eligibilityCriteria", "")]))
    add("eligibility", elig_full)


    # 4. Interventions
    interventions = protocol.get("armsInterventionsModule", {}).get("interventions", [])
    intv_lines = [
        f"{i.get('type','')}: {i.get('name','')} - {i.get('description','')}".strip(" -:")
        for i in interventions
    ]
    add("interventions", "\n".join(intv_lines))

    return chunks

def is_too_long(text, limit=256):
    return len(tok.encode(text)) > limit


def split_sentences(text):
    return [s for s in text.split("\n") if s.strip()]

def group_into_subchunks(sentences, limit=256):
    groups = []
    current = []
    for sentence in sentences:
        candidate = "\n".join(current + [sentence])
        if current and is_too_long(candidate, limit):
            groups.append("\n".join(current))
            current = [sentence]
        else:
            current.append(sentence)
    if current:
        groups.append("\n".join(current))
    return groups

def sub_chunk(chunk, limit=256):
    if not is_too_long(chunk["text"], limit):
        return [chunk]
    sentences = split_sentences(chunk["text"])
    groups = group_into_subchunks(sentences, limit)
    result = []
    for i, group in enumerate(groups):
        new_chunk = chunk.copy()
        new_chunk["text"] = group
        new_chunk["id"] = f"{chunk['id']}::part{i+1}"
        result.append(new_chunk)
    return result
