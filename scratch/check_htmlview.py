import urllib.request
import re

url = "https://docs.google.com/spreadsheets/d/1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4/htmlview"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8")
        # In htmlview, tabs are rendered in <ul id="sheet-menu"> or similar
        tabs = re.findall(r'<li[^>]*id=\"sheet-button-([^\"]+)\"[^>]*><a[^>]*>([^<]+)</a>', html)
        print("Tabs in htmlview:", tabs)
        if not tabs:
            # find all <li> or sheet buttons
            all_buttons = re.findall(r'sheet-button-[^>]+>([^<]+)<', html)
            print("Buttons:", all_buttons)
            # find any gid
            all_gids = re.findall(r'#gid=(\d+)', html)
            print("GIDs in links:", set(all_gids))
except Exception as e:
    print("Error:", e)
