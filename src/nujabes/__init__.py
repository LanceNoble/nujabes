from urllib.request import urlopen, Request
from io import open
from asyncio import run, sleep, create_task, timeout
from json import loads, dumps
from random import random

from websockets.asyncio.client import connect, ClientConnection
from websockets.exceptions import ConnectionClosed, ConcurrencyError, InvalidURI, InvalidProxy, InvalidHandshake

async def beat(client: ClientConnection, connectionState: dict[str, int]) -> bool:
    prevNumAcks = connectionState["numAcks"]
    await client.send(dumps({"op": 1, "d": connectionState["sequence"]}))
    await sleep(5)
    if connectionState["numAcks"] == prevNumAcks:
        await client.close()
        return False
    return True

async def repeat(interval: int, client: ClientConnection, connectionState: dict[str, int]):
    numBeats = 0
    while True:
        if numBeats == 0:
            await sleep(interval * random() / 1000)
        else:
            await sleep(interval / 1000)
        numBeats += 1
        if await beat(client, connectionState) == False:
            return

async def enter():
    stream = open("../../token")
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
    connectionState = {"numAcks": 0, "sequence": None}
    task1 = create_task(repeat(loads(await client.recv())["d"]["heartbeat_interval"], client, connectionState))
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
        return
    # while True:
    #     await client.recv()

    task1.cancel()

run(enter())
