import asyncio
import os

from aiohttp import web

try:
    import uvloop

    uvloop.install()
except ImportError:
    pass


async def ping(request):
    return web.json_response({"status": "ok"})


async def items(request):
    return web.json_response({"items": list(range(100))})


async def io(request):
    await asyncio.sleep(0.01)
    return web.json_response({"status": "ok"})


app = web.Application()
app.router.add_get("/ping", ping)
app.router.add_get("/items", items)
app.router.add_get("/io", io)


if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", "8000")))
