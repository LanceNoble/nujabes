from urllib.request import urlopen, Request
from io import open
from asyncio import run, sleep, create_task
from json import loads, dumps
from random import random

from websockets.asyncio.client import connect, ClientConnection

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

sequence = None

async def beat(client: ClientConnection, interval: int):
    numBeats = 0
    while True:
        if numBeats == 0:
            await sleep(interval * random() / 1000)
        else:
            await sleep(interval / 1000)
        await client.send(dumps({"op": 1, "d": sequence}))
        await client
        numBeats += 1

async def enter():
    client = await connect(f"{gate["url"]}/?v=10&encoding=json")
    task1 = create_task(beat(client, loads(await client.connection.recv())["d"]["heartbeat_interval"]))
    
    task1.cancel()

run(enter())

# r = requests.post(
#     "https://discord.com/api/v10/applications/1399145076931821689/commands",
#     headers={
#         "Authorization": "Bot"
#     },
#     json={
#         "name": "play",
#         "description": "play a song",
#         "options": [
#             {
#                 "type": 3,
#                 "name": "song",
#                 "description": "title or yt link",
#                 "required": True
#             }
#         ]
#     })
# print(r.content)

