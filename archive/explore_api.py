import requests

url = "https://clinicaltrials.gov/api/v2/studies"

params = {
    "query.lead": "Gilead Sciences", # trials where Gilead is the lead sponsor
    "countTotal": "true",            # ask the API for the total match count
    "pageSize": 1,                   # we only want to peek at one
    "format": "json",
}

data = requests.get(url, params=params, timeout=30).json()

print("Total Gilead-led trials:", data.get("totalCount"))

first = data["studies"][0]
title = first["protocolSection"]["identificationModule"]["briefTitle"]
print("First trial:", title)

