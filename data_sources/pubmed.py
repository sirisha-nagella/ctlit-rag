"""
Fetch paper abstracts from PubMed via NCBI E-utilities.
Two steps: ESearch (query -> PMIDs) then EFetch (PMIDs -> abstracts).
Public API, no key needed for low volume.
"""

import requests
import xml.etree.ElementTree as ET

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

TOOL = "ctlit-rag"
EMAIL = "sirisha.nagella@gmail.com" # our email ID

def _search_pmids(query, max_results):
    params = {
        "db": "pubmed", "term": query, "retmax": max_results,
        "retmode": "json", "tool": TOOL, 
        "email": EMAIL,
    }
    data = requests.get(ESEARCH, params=params, timeout=30).json()
    return data["esearchresult"]["idlist"]

def _fetch_abstracts(pmids):
    params = {
        "db": "pubmed", "id": ",".join(pmids),
        "retmode": "xml", "tool": TOOL,
        "email": EMAIL,
    }
    xml_text = requests.get(EFETCH, params=params, timeout=30).text
    root = ET.fromstring(xml_text)


    papers = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext("MedlineCitation/PMID")
        title = article.findtext("MedlineCitation/Article/ArticleTitle") or ""
        parts = [el.text or "" for el in
                 article.findall("MedlineCitation/Article/Abstract/AbstractText")]
        abstract = " ".join(parts).strip()

        if abstract:
            papers.append({"pmid": pmid, "title": title, "abstract": abstract})
    return papers


def search_papers(query, max_results=20):
    """Search PubMed and return a list of {pmid, title, abstract} dicts."""
    pmids = _search_pmids(query, max_results)
    if not pmids:
        return[]
    return _fetch_abstracts(pmids)

# self-test
if __name__ == "__main__":
    papers = search_papers("sofosbuvir velpatasvir hepatitis C", max_results=10)
    print(f"Fetched {len(papers)} papers with abstracts.")
    for p in papers[:3]:
        print(" -", p["pmid"], p["title"][:70])

