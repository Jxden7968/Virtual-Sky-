import asyncio, json, os, urllib.request

try:
    import websockets
except ImportError:
    websockets = None

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD = os.environ["GUILD_ID"]
INVITE = os.environ.get("INVITE_CODE", "DUebsA85n2")
HEADERS = {
    "Authorization": "Bot " + TOKEN,
    "User-Agent": "DiscordBot (virtual-sky-stats, 1.0)",
}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def get_public(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (virtual-sky-stats)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


# 1) Mitglieder und Bots zaehlen
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


# 2) Online-Zahl genau ueber das Gateway (Presence Intent noetig)
async def gateway_presences():
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"
    async with websockets.connect(uri, max_size=None) as ws:
        hello = json.loads(await ws.recv())
        interval = hello["d"]["heartbeat_interval"] / 1000
        await ws.send(json.dumps({
            "op": 2,
            "d": {
                "token": TOKEN,
                "intents": (1 << 0) | (1 << 8),  # GUILDS + GUILD_PRESENCES
                "properties": {"os": "linux", "browser": "virtual-sky", "device": "virtual-sky"},
            },
        }))
        loop = asyncio.get_event_loop()
        start = last_hb = loop.time()
        while loop.time() - start < 40:
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            except asyncio.TimeoutError:
                msg = None
            if loop.time() - last_hb > interval * 0.9:
                await ws.send(json.dumps({"op": 1, "d": None}))
                last_hb = loop.time()
            if not msg:
                continue
            if msg.get("op") in (7, 9):
                return None
            if msg.get("t") == "GUILD_CREATE" and msg["d"]["id"] == str(GUILD):
                return msg["d"].get("presences", [])
    return None


online = None
if websockets is not None:
    try:
        pres = asyncio.run(gateway_presences())
        if pres is not None:
            online = len([p for p in pres if p.get("status") in ("online", "idle", "dnd")])
            print("Online via Gateway ->", online)
        else:
            print("Gateway lieferte keine Praesenzen")
    except Exception as e:
        print("Online via Gateway fehlgeschlagen:", e)
else:
    print("Paket websockets fehlt, Gateway uebersprungen")

# 3) Falls das nicht klappt: Einladungslink / Widget (ungefaehr)
if online is None:
    quellen = [
        ("Einladung", f"https://discord.com/api/v10/invites/{INVITE}?with_counts=true", "approximate_presence_count"),
        ("Widget", f"https://discord.com/api/guilds/{GUILD}/widget.json", "presence_count"),
    ]
    for name, url, key in quellen:
        try:
            v = get_public(url).get(key)
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
