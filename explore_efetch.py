import requests
import xml.etree.ElementTree as ET

# the PMIDs you got from Esearch

pmids = ["42239969", "42158890", "42104765", "42089097", "42067387"]

url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
params = {
    "db": "pubmed",
    "id": ",".join(pmids),      # comma-joined IDs in one call
    "retmode": "xml",
    "tool": "ctlit-rag",
    "email": "sirisha.nagella@gmail.com", # your/my email again
}

xml_text = requests.get(url, params=params, timeout=30).text
root = ET.fromstring(xml_text)

for article in root.findall(".//PubmedArticle"):
    pmid = article.findtext("MedlineCitation/PMID")
    title = article.findtext("MedlineCitation/Article/ArticleTitle")

    # an abstract can be split into labelled sections; join them

    parts = [el.text or "" for el in 
             article.findall("MedlineCitation/Article/Abstract/AbstractText")]
    
    abstract = " ".join(parts).strip()

    print("PMID:    ", pmid)
    print("Title:   ", title)
    print("Abstract:", (abstract[:300] if abstract else "(no abstract)"), "...")
    print()
