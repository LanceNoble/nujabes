baseUrl = "https://discord.com/api/v10"
_stream = open("../../2token")
botToken = _stream.read()
_stream.close()
botHeaders = {
    "User-Agent": "nujabes (https://github.com/LanceNoble/nujabes, 1.0)",
    "Authorization": f"Bot {botToken}",
    "Content-Type": "application/json"
}