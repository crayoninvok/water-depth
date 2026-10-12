import urllib.request

GSHEET_ID = "1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4"

for gid in ["0", "222827428"]:
    url = f"https://docs.google.com/spreadsheets/d/{GSHEET_ID}/export?format=csv&gid={gid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            print(f"=== GID {gid} ===")
            print(f"Length: {len(content)}")
            lines = content.strip().split("\n")
            print(f"Total lines: {len(lines)}")
            for l in lines[:5]:
                print("Line:", l)
    except Exception as e:
        print(f"Error on GID {gid}: {e}")
