import urllib.request
import re
import json
import pandas as pd

SHEET_ID = "1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4"

def fetch_gsheet_df(sheet_id):
    # Method 1: Export CSV
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            if len(content) > 0:
                df = pd.read_csv(pd.io.common.BytesIO(content))
                if not df.empty and len(df.columns) > 1:
                    print("Fetched via CSV export, rows:", len(df))
                    return df
    except Exception as e:
        print("CSV export error:", e)

    # Method 2: GViz API
    try:
        gviz_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json"
        req = urllib.request.Request(gviz_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            clean_json = re.sub(r'/\*.*?\*/\s*google\.visualization\.Query\.setResponse\(|\);?\s*$', '', raw)
            data = json.loads(clean_json)
            cols = [c['label'] if c and 'label' in c and c['label'] else (c.get('id') if c else f"Col_{i}") for i, c in enumerate(data['table']['cols'])]
            rows = []
            for r in data['table']['rows']:
                row_vals = [c['v'] if c and 'v' in c else None for c in r['c']]
                rows.append(row_vals)
            df = pd.DataFrame(rows, columns=cols)
            if not df.empty and any(cols):
                print("Fetched via GViz, rows:", len(df))
                return df
    except Exception as e:
        print("GViz error:", e)
        
    return None

df = fetch_gsheet_df(SHEET_ID)
print("Result is None:", df is None)
