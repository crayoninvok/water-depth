import urllib.request
import re
import json

url = "https://docs.google.com/spreadsheets/d/1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4/edit"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8")
        
        # Look for sheet metadata in bootstrap data
        sheet_info = re.findall(r'(\d+),\"([^\"]+)\",\d+,\d+,\"[^\"]*\",\d+', html)
        print("Pattern 1:", sheet_info)
        
        # Check sheetNames or similar
        names = re.findall(r'\"name\":\s*\"([^\"]+)\"', html)
        print("Names found:", [n for n in names if len(n) < 30][:10])
        
        # Check for sheetId
        sids = re.findall(r'\"sheetId\":\s*(\d+)', html)
        print("SheetIds found:", sids[:10])
except Exception as e:
    print("Error:", e)
