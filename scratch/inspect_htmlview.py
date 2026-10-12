import urllib.request
import re

url = "https://docs.google.com/spreadsheets/d/1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4/htmlview"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=10) as resp:
    html = resp.read().decode("utf-8")
    print("Length of html:", len(html))
    # print any occurrence of 'sheet' or 'tab'
    matches = re.findall(r'<li[^>]*>.*?</li>', html, re.DOTALL)
    print("li matches:", len(matches))
    for m in matches[:10]:
        print("LI:", repr(m))
    # search for 'gid='
    gids = re.findall(r'gid=(\d+)', html)
    print("gids in html:", set(gids))
