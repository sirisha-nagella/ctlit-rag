
import json
from pathlib import Path

# pick any saved trial

path = Path("data/trials/NCT01590654.json")
study = json.loads(path.read_text())

ps = study["protocolSection"]

# the human-readable fields buried in the record

ident = ps["identificationModule"]
desc = ps.get("descriptionModule", {})
cond = ps.get("conditionsModule", {})
elig = ps.get("eligibilityModule", {})

print("NCT ID:   ", ident["nctId"])
print("Title:     ", ident["briefTitle"])
print("Conditions:", cond.get("conditions"))
print()
print("SUMMARY:")
print(desc.get("briefSummary", "(none)"))
print()
print("ELIGIBILITY (first 400 chars):")
print((elig.get("eligibilityCriteria", "(none)"))[:400])
