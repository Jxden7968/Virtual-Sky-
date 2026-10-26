import json, os, urllib.request

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD = os.environ["GUILD_ID"]
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

with open("stats.json", "w") as f:
    json.dump({"members": members, "bots": bots}, f)
print("members", members, "bots", bots)
