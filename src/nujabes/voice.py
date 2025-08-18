class Voice:
    def __init__(self, guild_id, channel_id):
        self._counter = 0
        self._guild_id = guild_id
        self._channel_id = channel_id
        self._sock = None
    