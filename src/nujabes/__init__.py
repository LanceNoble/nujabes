from requests import get, post
from io import open
from asyncio import run, sleep, create_task, create_subprocess_exec, Queue, Task
from asyncio.subprocess import PIPE
from json import loads, dumps
from random import random

from websockets.asyncio.client import connect, ClientConnection

from yt_dlp import YoutubeDL

async def beat(client: ClientConnection, connectionState: dict[str, int]):
    prevNumAcks = connectionState["numAcks"]
    await client.send(dumps({"op": 1, "d": connectionState["sequence"]}))
    await sleep(5)
    if connectionState["numAcks"] == prevNumAcks:
        await client.close()

async def repeat(interval: int, client: ClientConnection, connectionState: dict[str, int]):
    numBeats = 0
    while True:
        if numBeats == 0:
            await sleep(interval * random() / 1000)
        else:
            await sleep(interval / 1000)
        numBeats += 1
        await beat(client, connectionState)

async def process(events: Queue, botToken: str):
    while True:
        event = await events.get()
        response = get(
            f"https://discord.com/api/v10/guilds/{event['d']['guild_id']}/voice-states/@me",
            headers={
                "User-Agent": "nujabes (https://github.com/LanceNoble/Nujabes, 1.0)",
                "Authorization": f"Bot {botToken}",
                "Content-Type": "application/json"
            }
        )
        voiceState = response.json()
        if response.status_code == 404:
            pass
        elif event["d"]["guild_id"] != voiceState["channel_id"]:
            pass
        events.task_done()

async def respond(interactionId: str, interactionToken: str, botToken: str, guildId: str):
    response = get(
        f"https://discord.com/api/v10/guilds/{guildId}/voice-states/@me",
        headers={
            "User-Agent": "nujabes (https://github.com/LanceNoble/Nujabes, 1.0)",
            "Authorization": f"Bot {botToken}",
            "Content-Type": "application/json"
        }
    )
    if response.status_code == 404:
        create_task()
    voiceState = loads(response.read())
    
    # response = urlopen(Request(
    #     f"https://discord.com/api/v10/interactions/{interactionId}/{interactionToken}/callback",
    #     dumps({
    #         "type": 4,
    #         "data": {
    #             "content": "Congrats on sending your command!"
    #         }
    #     }).encode(),
    #     {
    #         "User-Agent": "nujabes (https://github.com/LanceNoble/Nujabes, 1.0)",
    #         "Authorization": f"Bot {interactionToken}",
    #         "Content-Type": "application/json"
    #     }
    # ))

async def enter():
    # ydl = YoutubeDL({ "format": "bestaudio", "skip_download": True })
    # info = ydl.extract_info("https://www.youtube.com/watch?v=iqPAVCtRO3I")
    # proc = await create_subprocess_exec(
    #     "../../bin/ffmpeg.exe", "-i", info["url"], "-c:a" , "libopus", "-ar", "48000", "-ac", "2", "-f", "opus", "pipe:1",
    #     stdout=PIPE
    # )
    # try:
    #     while True:
    #         chunk = await proc.stdout.read(4096)
    #         if not chunk:
    #             break
    #         # Process the chunk (e.g., write to file, analyze, etc.)
    #         print(f"Received {len(chunk)} bytes")
    # finally:
    #     await proc.wait()
    # ydl.close()

    stream = open("../../token")
    botToken = stream.read()
    stream.close()

    response = get(
        "https://discord.com/api/v10/gateway/bot",
        headers={
            "User-Agent": "nujabes (https://github.com/LanceNoble/Nujabes, 1.0)",
            "Authorization": f"Bot {botToken}"
        }
    )
    gate = response.json()
    # b'{"url":"wss://gateway.discord.gg","session_start_limit":{"max_concurrency":1,"remaining":1000,"reset_after":0,"total":1000},"shards":1}\n'

    client = await connect(f"{gate['url']}/?v=10&encoding=json")
    heartbeat = loads(await client.recv())

    await client.send(dumps({
        "op": 2,
        "d": {
            "token": botToken,
            "intents": 0,
            "properties": {
                "os": "windows",
                "browser": "nujabes",
                "device": "nujabes"
            }
        }
    }))

    ready = loads(await client.recv())
    if ready["op"] == 9:
        client.close()
        return

    processors: list[Task] = []
    eventMap: dict[str, Queue] = {}
    for guild in ready["d"]["guilds"]:
        eventMap[guild["id"]] = Queue()
        processors.append(create_task(process(eventMap[guild["id"]], botToken)))

    connectionState = {"numAcks": 0, "sequence": None}
    interval = create_task(repeat(heartbeat["d"]["heartbeat_interval"], client, connectionState))

    while True:
        event = loads(await client.recv())
        print(event)
        if event["op"] == 0:
            # task = create_task(respond(event["d"]["id"], event["d"]["token"], token, event["d"]["guild_id"]))
            # eventMap[event["d"]["guild_id"]].put(event)
            connectionState["sequence"] = event["s"]
        elif event["op"] == 1:
            create_task(beat())
        elif event["op"] == 11:
            connectionState["numAcks"] += 1
        
    interval.cancel()
    for acoiewj in processors:
        acoiewj.cancel()

run(enter())
