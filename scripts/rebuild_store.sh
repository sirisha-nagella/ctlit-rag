#!/usr/bin/env bash
#
# Rebuild the Chroma vector store from scratch.
# chroma_store/ is intentionally NOT committed to git, so this script is the
# reproducible source of truth for it. Run from the project root:
#
#   ./scripts/rebuild_store.sh
#
set -euo pipefail

echo "1/3  Fetching Gilead trials from ClinicalTrials.gov -> data/trials/ ..."
python -m scripts.fetch_trials

echo "2/3  Chunking + embedding trials into chroma_store/ ..."
python -m scripts.load_vector_store

echo "3/3  Adding PubMed literature to the same store ..."
python -m scripts.load_literature

echo "Done. chroma_store/ rebuilt."
