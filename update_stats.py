import json, os, urllib.request

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD = os.environ["GUILD_ID"]
INVITE = os.environ.get("INVITE_CODE", "qt9qMv7")
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

# Online-Zahl aus dem Einladungslink (ungefaehr, kein Extra-Recht noetig)
try:
    inv = get(f"https://discord.com/api/v10/invites/{INVITE}?with_counts=true")
    online = inv.get("approximate_presence_count")
    if online is not None:
        data["online"] = online
except Exception as e:
    print("Online-Zahl nicht geladen:", e)

with open("stats.json", "w") as f:
    json.dump(data, f)
print(data)
