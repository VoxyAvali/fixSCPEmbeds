import json
import requests

TITLES = {}

def load_scp_titles():
    global TITLES
    try:
        r = requests.get("https://scp-data.tedivm.com/data/scp/items/index.json")
        data = r.json()
        
        for item in data.get("items", []):
            scp_id = item.get("scp")
            title = item.get("title", "Unknown")
            TITLES[scp_id.lower()] = f"{scp_id} - {title}"
    except:
        pass 

load_scp_titles()
