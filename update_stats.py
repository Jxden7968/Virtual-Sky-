import json, os, urllib.request

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD = os.environ["GUILD_ID"]
INVITE = os.environ.get("INVITE_CODE", "DUebsA85n2")
HEADERS = {
    "Authorization": "Bot " + TOKEN,
    "User-Agent": "DiscordBot (virtual-sky-stats, 1.0)",
}

def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

members = bots = 0
after = "0"
while True:
    page = get(f"https://discord.com/api/v10/guilds/{GUILD}/members?limit=1000&after={after}")
    if not page:
        break
    for m in page:
        if m["user"].get("bot"):
            bots += 1
        else:
            members += 1
    after = page[-1]["user"]["id"]
    if len(page) < 1000:
        break

data = {"members": members, "bots": bots}

# Online-Zahl holen (oeffentlich, ohne Bot-Token)
def get_public(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (virtual-sky-stats)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

online = None
quellen = [
    ("Einladung", f"https://discord.com/api/v10/invites/{INVITE}?with_counts=true", "approximate_presence_count"),
    ("Widget", f"https://discord.com/api/guilds/{GUILD}/widget.json", "presence_count"),
]
for name, url, key in quellen:
    try:
        d = get_public(url)
        v = d.get(key)
        print("Online via", name, "->", v)
        if v is not None:
            online = v
            break
    except Exception as e:
        print("Online via", name, "fehlgeschlagen:", e)

if online is not None:
    data["online"] = online
else:
    print("Keine Online-Zahl gefunden")

with open("stats.json", "w") as f:
    json.dump(data, f)
print(data)
