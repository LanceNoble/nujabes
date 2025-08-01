from urllib.request import urlopen, Request
from io import open
from asyncio import run, sleep, create_task, create_subprocess_exec
from asyncio.subprocess import PIPE
from json import loads, dumps
from random import random
from tempfile import TemporaryFile

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

async def respond(id: str, token: str):
    #fp = TemporaryFile()

    response = urlopen(Request(
        f"https://discord.com/api/v10/interactions/{id}/{token}/callback",
        data=dumps({
            "type": 4,
            "data": {
                "content": "Congrats on sending your command!"
            }
        }).encode(),
        headers={
            "User-Agent": "nujabes (https://github.com/LanceNoble/Nujabes, 1.0)",
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }
    ))

async def enter():
    ydl = YoutubeDL({
        "format": "bestaudio",
        "skip_download": True,
    })
    info = ydl.extract_info("https://www.youtube.com/watch?v=iqPAVCtRO3I")
    proc = await create_subprocess_exec(
        "../../bin/ffmpeg.exe", "-i", info["url"], "-c:a" , "libopus", "-ar", "48000", "-ac", "2", "-f", "opus", "pipe:1",
        stdout=PIPE
    )
    try:
        while True:
            chunk = await proc.stdout.read(4096)
            if not chunk:
                break
            # Process the chunk (e.g., write to file, analyze, etc.)
            print(f"Received {len(chunk)} bytes")
    finally:
        await proc.wait()
    ydl.close()
    #await proc.communicate()

    stream = open("token")
    token = stream.read()
    stream.close()

    response = urlopen(Request(
        "https://discord.com/api/v10/gateway/bot",
        headers={
            "User-Agent": "nujabes (https://github.com/LanceNoble/Nujabes, 1.0)",
            "Authorization": f"Bot {token}"
        }
    ))
    gate = loads(response.read())
    response.close()
    # b'{"url":"wss://gateway.discord.gg","session_start_limit":{"max_concurrency":1,"remaining":1000,"reset_after":0,"total":1000},"shards":1}\n'

    client = await connect(f"{gate['url']}/?v=10&encoding=json")
    heartbeat = loads(await client.recv())
    await client.send(dumps({
        "op": 2,
        "d": {
            "token": token,
            "intents": 0,
            "properties": {
                "os": "windows",
                "browser": "nujabes",
                "device": "nujabes"
            }
        }
    }))
    idValidationResult = loads(await client.recv())
    if idValidationResult["op"] == 9:
        client.close()
        return
    connectionState = {"numAcks": 0, "sequence": None}
    task1 = create_task(repeat(heartbeat["d"]["heartbeat_interval"], client, connectionState))

    while True:
        message = loads(await client.recv())
        print(message)
        if message["op"] == 0:
            connectionState["sequence"] = message["s"]
            create_task(respond(message["d"]["id"], message["d"]["token"]))
        elif message["op"] == 1:
            create_task(beat())
        elif message["op"] == 11:
            connectionState["numAcks"] += 1

    task1.cancel()

run(enter())
