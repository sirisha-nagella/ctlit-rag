"""ClinicalTrials.gov data source."""

"""
Fetch clinical trial records from ClinicalTrials.gov API v2.
Public API, no auth. We page through results with nextpageToken.
"""

import requests

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

def search_trials(condition=None, sponsor=None, max_trials=25, page_size=25):
    """Return a list of raw study records (dicts)."""
    params = {
        "format": "json",
        "pageSize": min(page_size, max_trials),
        "countTotal": "true",
    }
    if condition:
        params["query.cond"] = condition # e.g. "multiple myeloma"
    if sponsor:
        params["query.lead"] = sponsor  # e.g. "Gilead Sciences"

    studies = []
    while len(studies) < max_trials:
        data = requests.get(BASE_URL, params=params, timeout=30).json()
        studies.extend(data.get("studies", []))

        token = data.get("nextPageToken")
        if not token:
            break
        params["pageToken"] =   token

    return studies[:max_trials]

#quick self-test: run this file directly to check it works
if __name__ == "__main__":
    trials = search_trials(sponsor="Gilead Sciences", max_trials=25)
    print(f"Fetched {len(trials)} trials.")
    for study in trials[:5]:
        title = study["protocolSection"]["identificationModule"]["briefTitle"]
        print(" -", title)

        