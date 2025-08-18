from requests import get
from json import loads, dumps
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed
from os import name
from asyncio import create_task, sleep, run
from random import random
from voice import Voice

class Client:
    def __init__(self, name, website, version, token):
        self._base = "https://discord.com/api/v10"
        self._headers = {
            "User-Agent": f"{name} ({website}, {version})",
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }
        self._name = name
        self._website = website
        self._version = version
        self._token = token
        self._sock = None

    def add_slash_handler(self, coro):
        setattr(self, coro.__name__, coro)  

    async def join(self, guild, channel):
        await self._sock.send(dumps({
            "op": 4,
            "d": { "guild_id": guild, "channel_id": channel, "self_mute": False, "self_deaf": False }
        }))

    async def connect(self):
        gate = get(f"{self._base}/gateway/bot", headers=self._headers).json()
        self._sock = await connect(f"{gate['url']}/?v=10&encoding=json")
        hello = loads(await self._sock.recv())
        await self._sock.send(dumps({
            "op": 2,
            "d": {
                "token": self._token,
                "intents": 0,
                "properties": { "os": name, "browser": self._name, "device": self._name }
            }
        }))
        ready = loads(await self._sock.recv())
        for guild_id in ready["d"]["guilds"]:
            setattr(self, guild_id, Voice())
        resumeUrl = ready["d"]["resume_gateway_url"]
        curr_ack = 0
        curr_seq = ready["s"]
        async def beat():
            prev_ack = curr_ack
            await self._sock.send(dumps({"op": 1, "d": curr_seq}))
            await sleep(5)
            if curr_ack == prev_ack:
                await self._sock.close()
        async def repeat():
            num_beats = 0
            while True:
                if num_beats == 0:
                    await sleep(hello["d"]["heartbeat_interval"] * random() / 1000)
                else:
                    await sleep(hello["d"]["heartbeat_interval"] / 1000)
                num_beats += 1
                await beat()
        interval = create_task(repeat())
        while True:
            event = None
            try:
                event = loads(await self._sock.recv())
            except ConnectionClosed as e:
                print(e)
            print(event)
            if event["op"] == 0:
                curr_seq = event["s"]
                if event["t"] == "INTERACTION_CREATE" and event["d"]["type"] == 2:
                    create_task(getattr(self, event["d"]["data"]["name"])(event["d"]))
                elif event["t"] == "VOICE_SERVER_UPDATE" or event["t"] == "VOICE_STATE_UPDATE":
                    guild = event["d"]["guild_id"]
                    voice = getattr(guild)
                    voice._counter += 1
                    
                    print("")
            elif event["op"] == 1:
                create_task(beat())
            # elif event["op"] == 7:
            #     pass
            elif event["op"] == 11:
                curr_ack += 1
