from requests import get, post
from io import open
from asyncio import run, sleep, create_task, create_subprocess_exec, Queue, Task
from asyncio.subprocess import PIPE
from json import loads, dumps
from random import random

from websockets.asyncio.client import connect, ClientConnection
from websockets.exceptions import ConnectionClosed

from yt_dlp import YoutubeDL

from constants import baseUrl, botToken, botHeaders

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

async def process(events: Queue):
    while True:
        event = await events.get()
        #if ()
        response = get(f"{baseUrl}/guilds/{event['d']['guild_id']}/voice-states/@me", headers=botHeaders)
        voiceState = response.json()
        if response.status_code == 404:
            pass
        elif event["d"]["guild_id"] != voiceState["channel_id"]:
            pass
        events.task_done()

async def enter():
    gate = get(f"{baseUrl}/gateway/bot", headers=botHeaders).json()
    client = await connect(f"{gate['url']}/?v=10&encoding=json")
    hello = loads(await client.recv())

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
    resumeUrl = ready["d"]["resume_gateway_url"]

    processors: list[Task] = []
    eventMap: dict[str, Queue] = {}
    for guild in ready["d"]["guilds"]:
        eventMap[guild["id"]] = Queue()
        processors.append(create_task(process(eventMap[guild["id"]])))

    connectionState = {"numAcks": 0, "sequence": ready["s"]}
    interval = create_task(repeat(hello["d"]["heartbeat_interval"], client, connectionState))

    while True:
        event
        try:
            event = loads(await client.recv())
        except ConnectionClosed as e:
            pass
        if event["op"] == 0:
            eventMap[event["d"]["guild_id"]].put(event)
            connectionState["sequence"] = event["s"]
        elif event["op"] == 1:
            create_task(beat())
        elif event["op"] == 7:
            pass
        elif event["op"] == 11:
            connectionState["numAcks"] += 1
        
    interval.cancel()
    for process in processors:
        process.cancel()

async def foo():
    while True:
        await sleep(1)
        print("foo")

create_task(foo())
while True:
    pass

#run(enter())
