import requests
import urllib.request

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwwFYKKp8q-6BFgJldMO1GCX1GeHviWa3dVbigrCoq22aebjVM7w6OyOE_yY6trRQE/exec"
GSHEET_ID = "1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4"

payload = {
    "sheet": "Sheet2",
    "sheetName": "Sheet2",
    "gid": "222827428",
    "ID": 1,
    "Tanggal": "2026-10-12",
    "Waktu": "08:00",
    "Titik Pantau": "Jetty Muara Pahu",
    "Kedalaman Aktual (m)": 2.5,
    "Plan Kedalaman (m)": 4.0,
    "Status": "Surut (Tugboat Tidak Bisa Masuk)",
    "Petugas": "Dzaky",
    "Keterangan": "Test Muara Pahu"
}

resp = requests.post(WEBHOOK_URL, json=payload, timeout=12)
print("Webhook Response:", resp.status_code, resp.text)

# Now check both GID 0 and GID 222827428
for gid, name in [("0", "Sheet1 / Senyiur"), ("222827428", "Sheet2 / Muara Pahu")]:
    url = f"https://docs.google.com/spreadsheets/d/{GSHEET_ID}/export?format=csv&gid={gid}"
    with urllib.request.urlopen(url) as r:
        txt = r.read().decode("utf-8")
        print(f"=== {name} (gid={gid}) ===")
        print(f"Lines: {len(txt.strip().splitlines())}")
        if txt.strip():
            print("Last line:", txt.strip().splitlines()[-1])
