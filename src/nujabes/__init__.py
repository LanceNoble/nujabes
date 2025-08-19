from requests import get, post
from asyncio import run, sleep, create_task, create_subprocess_exec, Queue, Task
from asyncio.subprocess import PIPE
from json import loads, dumps
from random import random

from yt_dlp import YoutubeDL
from client import Client

# stream = open("token")
# token = stream.read()
# stream.close()

# foo = Client("nujabes", "https://github.com/LanceNoble/nujabes", "1.0", token)

# async def play(context):
    
#     pass
# foo.add_slash_handler(play)

# foo.connect()

bar = YoutubeDL()
bar.extract_info()