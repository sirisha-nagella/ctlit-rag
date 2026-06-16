
"""
Pull Gilead trials and save each as raw JSON in data/trials/.
Run from the project root: python3 -m scripts.fetch_trials
"""

import json
from pathlib import Path

from data_sources.clinicaltrials import search_trials

OUT_DIR = Path("data/trials")

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    trials = search_trials(sponsor="Gilead Sciences", max_trials=25)
    print(f"Fetched {len(trials)} trials.")

    for study in trials:
        nct_id = study["protocolSection"]["identificationModule"]["nctId"]
        (OUT_DIR / f"{nct_id}.json").write_text(json.dumps(study, indent=2))

    print(f"Saved {len(trials)} files to {OUT_DIR}/")

if __name__ == "__main__":
    main()


