import urllib.request
import urllib.parse

GSHEET_ID = "1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4"

test_sheets = [
    "Sheet1",
    "Senyiur",
    "Muara Pahu",
    "Jetty Senyiur",
    "Jetty Muara Pahu",
    "muara pahu",
    "senyiur"
]

for name in test_sheets:
    encoded = urllib.parse.quote(name)
    url = f"https://docs.google.com/spreadsheets/d/{GSHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8")
            print(f"Sheet '{name}': Status 200, Length: {len(content)}, Preview: {repr(content[:60])}")
    except urllib.error.HTTPError as e:
        print(f"Sheet '{name}': HTTP Error {e.code}")
    except Exception as e:
        print(f"Sheet '{name}': Error {e}")
