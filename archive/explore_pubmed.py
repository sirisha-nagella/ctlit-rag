import requests

url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

params = {
    "db": "pubmed",
    "term": "sofosbuvir velpatasvir hepatitis C",
    "retmax": 5,           # just the top 5 IDs for now
    "retmode": "json",
    "tool": "ctlit-rag",   # NCBI asks you to identify your tool
    "email": "sirisha.nagella@gmail.com",  # and give a contact email (your email)
}

data = requests.get(url, params=params, timeout=30).json()

result = data["esearchresult"]
print("Total matches:", result["count"])
print("PMIDs:", result["idlist"])

