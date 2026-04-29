import asyncio
import os

from sanic import Sanic
from sanic.response import json


app = Sanic("app")


@app.get("/ping")
async def ping(request):
    return json({"status": "ok"})


@app.get("/items")
async def items(request):
    return json({"items": list(range(100))})


@app.get("/io")
async def io(request):
    await asyncio.sleep(0.01)
    return json({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", "8000")), access_log=False)
