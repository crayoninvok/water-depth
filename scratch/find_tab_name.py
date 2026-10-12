import urllib.request
import re

url = "https://docs.google.com/spreadsheets/d/1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4/edit"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=10) as resp:
    html = resp.read().decode("utf-8")
    # Search around '222827428'
    idx = html.find("222827428")
    if idx != -1:
        print("Surrounding 222827428:", repr(html[max(0, idx-100):min(len(html), idx+100)]))
    else:
        print("222827428 not found in edit url")
