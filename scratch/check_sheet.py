import urllib.request
import re
import json

url = "https://docs.google.com/spreadsheets/d/1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4/edit?usp=sharing"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

with urllib.request.urlopen(req) as resp:
    html = resp.read().decode("utf-8", errors="ignore")

# Find sheet names and grid IDs
for m in re.finditer(r'\"([^\"]+)\",(\d+),\d+,\[\],\"gid=(\d+)\"', html):
    print(m.groups())

# Alternative regex for sheet metadata
gids = re.findall(r'gid=(\d+)', html)
print("Unique GIDs in page:", set(gids))

# Let's check visualization / gviz endpoint
sheet_id = "1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4"
gviz_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json"
req_gviz = urllib.request.Request(gviz_url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req_gviz) as resp:
        gviz_text = resp.read().decode("utf-8", errors="ignore")
        print("GViz text length:", len(gviz_text))
        # parse json from /*O_o*/ google.visualization.Query.setResponse(...);
        clean_json = re.sub(r'/\*.*?\*/\s*google\.visualization\.Query\.setResponse\(|\);?\s*$', '', gviz_text)
        data = json.loads(clean_json)
        cols = [c['label'] if 'label' in c else c.get('id') for c in data['table']['cols']]
        print("GViz Cols:", cols)
        rows = data['table']['rows']
        print(f"GViz Rows count: {len(rows)}")
        for r in rows[:5]:
            print([c['v'] if c and 'v' in c else None for c in r['c']])
except Exception as e:
    print("GViz error:", e)
